"""Provider-agnostic AI layer for the Project module.

The AI layer is *assistive, not authoritative*: it proposes tasks and assesses
whether a tracked task looks done. A human always confirms.

Design:

* ``AIProvider`` — abstract base defining the two operations the rest of the app
  depends on, plus ``test_connection``.
* ``AnthropicProvider`` / ``OpenAIProvider`` — concrete HTTP clients. ``Custom`` is
  served by ``OpenAIProvider`` against a user-supplied OpenAI-compatible base URL.
* ``NullProvider`` — returned when the AI layer is disabled; every operation is a
  graceful no-op so callers never need to special-case "AI off".
* ``get_provider(settings)`` — factory that reads ``Project AI Settings`` and returns
  the right instance.

Network calls live only in the concrete providers and are made lazily, so importing
this module (and running the deterministic scanner) never requires the AI stack.
Tests mock the provider rather than the network.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass

import frappe


@dataclass
class ProposedTask:
	"""An AI-proposed task, before it becomes a Project Task record."""

	title: str
	description: str = ""
	priority: str = "Medium"
	confidence: float = 0.0
	file_path: str | None = None
	line_number: int | None = None


@dataclass
class CompletionVerdict:
	"""The AI's assessment of whether a task is done."""

	done: bool
	confidence: float
	reasoning: str = ""
	uncertain: bool = False


class AIProvider(ABC):
	"""Common interface every provider implements."""

	def __init__(self, model: str, base_url: str, api_key: str | None, *, max_tokens: int, timeout: int):
		self.model = model
		self.base_url = base_url.rstrip("/")
		self.api_key = api_key
		self.max_tokens = max_tokens
		self.timeout = timeout

	@abstractmethod
	def _complete(self, system: str, user: str) -> str:
		"""Send one prompt and return the model's raw text response."""

	def discover_todos(self, scope: str) -> list[ProposedTask]:
		"""Propose tasks from a chunk of source context (diffs/files/notes)."""
		system = (
			"You are a senior engineer triaging a codebase. Identify concrete, "
			"actionable pending tasks. Respond ONLY with a JSON array of objects "
			"with keys: title, description, priority (Low|Medium|High|Urgent), "
			"confidence (0-1)."
		)
		raw = self._complete(system, scope)
		return [
			ProposedTask(
				title=item.get("title", "").strip(),
				description=item.get("description", ""),
				priority=item.get("priority", "Medium"),
				confidence=float(item.get("confidence", 0.0)),
			)
			for item in _safe_json_list(raw)
			if item.get("title")
		]

	def assess_completion(self, task_context: str) -> CompletionVerdict:
		"""Judge whether the described task looks complete given repo context."""
		system = (
			"You decide whether a software task is complete based on the provided "
			"repository context. Respond ONLY with a JSON object with keys: "
			"done (bool), confidence (0-1), reasoning (string), uncertain (bool)."
		)
		raw = self._complete(system, task_context)
		obj = _safe_json_object(raw)
		return CompletionVerdict(
			done=bool(obj.get("done", False)),
			confidence=float(obj.get("confidence", 0.0)),
			reasoning=str(obj.get("reasoning", "")),
			uncertain=bool(obj.get("uncertain", False)),
		)

	def test_connection(self) -> dict:
		"""Light round-trip to validate credentials/endpoint."""
		if not self.api_key:
			return {"ok": False, "message": "No API key resolved (field, site_config, or env)."}
		try:
			self._complete("Reply with the single word: ok.", "ping")
		except Exception as exc:  # surfaced to the user, not raised
			return {"ok": False, "message": f"{type(exc).__name__}: {exc}"}
		return {"ok": True, "message": f"Reached {self.__class__.__name__} ({self.model})."}


class NullProvider(AIProvider):
	"""Used when the AI layer is disabled. Every operation is a no-op."""

	def __init__(self):
		super().__init__("", "", None, max_tokens=0, timeout=0)

	def _complete(self, system: str, user: str) -> str:
		return ""

	def discover_todos(self, scope: str) -> list[ProposedTask]:
		return []

	def assess_completion(self, task_context: str) -> CompletionVerdict:
		return CompletionVerdict(done=False, confidence=0.0, reasoning="AI layer disabled.", uncertain=True)

	def test_connection(self) -> dict:
		return {"ok": False, "message": "AI layer is disabled."}


class AnthropicProvider(AIProvider):
	"""Anthropic Messages API client."""

	def _complete(self, system: str, user: str) -> str:
		import requests

		resp = requests.post(
			f"{self.base_url}/v1/messages",
			headers={
				"x-api-key": self.api_key or "",
				"anthropic-version": "2023-06-01",
				"content-type": "application/json",
			},
			json={
				"model": self.model,
				"max_tokens": self.max_tokens,
				"system": system,
				"messages": [{"role": "user", "content": user}],
			},
			timeout=self.timeout,
		)
		resp.raise_for_status()
		data = resp.json()
		parts = data.get("content", [])
		return "".join(p.get("text", "") for p in parts if p.get("type") == "text")


class OpenAIProvider(AIProvider):
	"""OpenAI Chat Completions client. Also serves Custom (OpenAI-compatible) endpoints."""

	def _complete(self, system: str, user: str) -> str:
		import requests

		resp = requests.post(
			f"{self.base_url}/chat/completions",
			headers={
				"Authorization": f"Bearer {self.api_key or ''}",
				"content-type": "application/json",
			},
			json={
				"model": self.model,
				"max_tokens": self.max_tokens,
				"messages": [
					{"role": "system", "content": system},
					{"role": "user", "content": user},
				],
			},
			timeout=self.timeout,
		)
		resp.raise_for_status()
		data = resp.json()
		return data["choices"][0]["message"]["content"]


_PROVIDER_CLASSES = {
	"Claude (Anthropic)": AnthropicProvider,
	"ChatGPT (OpenAI)": OpenAIProvider,
	"Custom": OpenAIProvider,
}


def get_provider(settings=None) -> AIProvider:
	"""Build the configured provider from ``Project AI Settings``.

	Returns ``NullProvider`` when the AI layer is disabled, so callers can invoke
	``discover_todos`` / ``assess_completion`` unconditionally.
	"""
	settings = settings or frappe.get_single("Project AI Settings")
	if not settings.enabled:
		return NullProvider()

	cls = _PROVIDER_CLASSES[settings.provider]
	return cls(
		model=settings.resolved_model(),
		base_url=settings.resolved_base_url(),
		api_key=settings.resolved_api_key(),
		max_tokens=settings.max_tokens or 1024,
		timeout=settings.request_timeout or 60,
	)


def _safe_json_list(raw: str) -> list[dict]:
	data = _safe_json(raw)
	return data if isinstance(data, list) else []


def _safe_json_object(raw: str) -> dict:
	data = _safe_json(raw)
	return data if isinstance(data, dict) else {}


def _safe_json(raw: str):
	"""Parse model output as JSON, tolerating ```json fences and surrounding prose."""
	if not raw:
		return None
	text = raw.strip()
	if text.startswith("```"):
		text = text.strip("`")
		text = text.split("\n", 1)[1] if "\n" in text else text
	# Grab the outermost JSON array/object if the model added prose around it.
	for opener, closer in (("[", "]"), ("{", "}")):
		start = text.find(opener)
		end = text.rfind(closer)
		if start != -1 and end != -1 and end > start:
			try:
				return json.loads(text[start : end + 1])
			except json.JSONDecodeError:
				continue
	try:
		return json.loads(text)
	except json.JSONDecodeError:
		frappe.log_error("Project AI: could not parse provider response as JSON")
		return None
