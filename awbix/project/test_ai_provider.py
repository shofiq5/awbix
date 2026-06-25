from unittest.mock import MagicMock, patch

from frappe.tests.utils import FrappeTestCase

from awbix.project.ai_provider import (
	AnthropicProvider,
	CompletionVerdict,
	NullProvider,
	OpenAIProvider,
	ProposedTask,
	_safe_json,
)


class _Recorder(AnthropicProvider):
	"""Captures the prompt instead of calling the network."""

	last_system = None
	last_user = None
	reply = "[]"

	def _complete(self, system, user):
		self.last_system = system
		self.last_user = user
		return self.reply


class TestNullProvider(FrappeTestCase):
	def test_noops(self):
		p = NullProvider()
		self.assertEqual(p.discover_todos("anything"), [])
		verdict = p.assess_completion("anything")
		self.assertFalse(verdict.done)
		self.assertTrue(verdict.uncertain)
		self.assertFalse(p.test_connection()["ok"])


class TestDiscoverAndAssess(FrappeTestCase):
	def _provider(self, reply):
		p = _Recorder("m", "https://x", "key", max_tokens=10, timeout=5)
		p.reply = reply
		return p

	def test_discover_todos_parses_array(self):
		p = self._provider('[{"title": "Do X", "priority": "High", "confidence": 0.7}]')
		tasks = p.discover_todos("some scope")
		self.assertEqual(len(tasks), 1)
		self.assertEqual(tasks[0].title, "Do X")
		self.assertEqual(tasks[0].priority, "High")
		self.assertAlmostEqual(tasks[0].confidence, 0.7)

	def test_discover_skips_titleless_items(self):
		p = self._provider('[{"description": "no title"}]')
		self.assertEqual(p.discover_todos("scope"), [])

	def test_assess_completion_parses_object(self):
		p = self._provider('{"done": true, "confidence": 0.9, "reasoning": "gone"}')
		verdict = p.assess_completion("ctx")
		self.assertTrue(verdict.done)
		self.assertAlmostEqual(verdict.confidence, 0.9)
		self.assertEqual(verdict.reasoning, "gone")


class TestProviderRequestShaping(FrappeTestCase):
	def test_anthropic_request_shape(self):
		with patch("requests.post") as post:
			post.return_value = MagicMock(
				raise_for_status=lambda: None,
				json=lambda: {"content": [{"type": "text", "text": "ok"}]},
			)
			p = AnthropicProvider(
				"claude-opus-4-8", "https://api.anthropic.com", "secret", max_tokens=42, timeout=9
			)
			out = p._complete("sys", "usr")

			self.assertEqual(out, "ok")
			_, kwargs = post.call_args
			self.assertEqual(kwargs["headers"]["x-api-key"], "secret")
			self.assertEqual(kwargs["json"]["model"], "claude-opus-4-8")
			self.assertEqual(kwargs["json"]["max_tokens"], 42)
			self.assertEqual(kwargs["json"]["system"], "sys")
			self.assertEqual(kwargs["timeout"], 9)
			self.assertTrue(post.call_args[0][0].endswith("/v1/messages"))

	def test_openai_request_shape(self):
		with patch("requests.post") as post:
			post.return_value = MagicMock(
				raise_for_status=lambda: None,
				json=lambda: {"choices": [{"message": {"content": "hi"}}]},
			)
			p = OpenAIProvider("gpt-4o", "https://api.openai.com/v1", "tok", max_tokens=7, timeout=3)
			out = p._complete("sys", "usr")

			self.assertEqual(out, "hi")
			_, kwargs = post.call_args
			self.assertEqual(kwargs["headers"]["Authorization"], "Bearer tok")
			self.assertEqual(kwargs["json"]["model"], "gpt-4o")
			self.assertEqual(kwargs["json"]["messages"][0]["role"], "system")
			self.assertTrue(post.call_args[0][0].endswith("/chat/completions"))


class TestJsonParsing(FrappeTestCase):
	def test_handles_code_fence_and_prose(self):
		raw = 'Sure!\n```json\n[{"title": "X"}]\n```\nDone.'
		self.assertEqual(_safe_json(raw), [{"title": "X"}])

	def test_returns_none_on_garbage(self):
		with patch("frappe.log_error"):
			self.assertIsNone(_safe_json("not json at all"))


class TestDataclasses(FrappeTestCase):
	def test_defaults(self):
		self.assertEqual(ProposedTask(title="t").priority, "Medium")
		self.assertFalse(CompletionVerdict(done=False, confidence=0.0).uncertain)
