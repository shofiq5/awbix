"""Abstract outbound handler (composer engine — wired in M5)."""


class BaseComposer:
	message_type: str | None = None
	version: str | None = None

	def compose(self, source_doc) -> str:
		"""Build raw outbound message text from a business document."""
		raise NotImplementedError

	def verify(self, raw: str) -> list[dict]:
		"""Self-check composed output; return issues (same shape as BaseParser.validate)."""
		return []
