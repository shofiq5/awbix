"""Abstract connectivity adapter (transports — wired in M4).

One instance is bound to one ``EDX Connection``. ``poll()`` must only *fetch* and
return raw payloads — staging, classification and processing happen in the pipeline,
so the transport stays dumb and fast under load.
"""


class BaseTransport:
	def __init__(self, connection):
		self.connection = connection

	def test(self, direction: str = "Inbound") -> dict:
		"""Return ``{"ok": bool, "message": str}`` with no side effects on stored data."""
		raise NotImplementedError

	def poll(self) -> list[dict]:
		"""Inbound: fetch new messages.

		Each item: ``{"raw", "sender", "subject", "external_id"}``.
		"""
		return []

	def send(self, raw: str, meta: dict) -> dict:
		"""Outbound: deliver one message; return ``{"ok", "external_id", "response"}``."""
		raise NotImplementedError
