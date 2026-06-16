"""Abstract inbound handler.

Concrete parsers live under ``awbix.edx.handlers.<family>`` and are bound to a
``(message_type, version)`` through an ``EDX Message Definition`` row — the engine
never imports them directly. Every method except ``process()`` must be free of side
effects (no DB writes, no network) so ``verify`` is safe to run repeatedly.
"""


class BaseParser:
	message_type: str | None = None
	version: str | None = None

	def parse(self, raw: str) -> dict:
		"""Turn raw message text into a normalized, JSON-serialisable dict.

		Pure and deterministic. The result is what ``EDX Message In.parsed_json``
		shows for human verification.
		"""
		raise NotImplementedError

	def business_key(self, data: dict) -> str | None:
		"""Stable business identity of the message (e.g. AWB number).

		Drives amendment / re-received detection. ``None`` means the message has no
		natural key and every occurrence is treated as new.
		"""
		return None

	def validate(self, data: dict) -> list[dict]:
		"""Return a list of issues; empty means the message verifies cleanly.

		Each issue: ``{"level": "Info|Warning|Error", "code", "message", "field"}``.
		An ``Error`` issue blocks processing.
		"""
		return []

	def process(self, data: dict, message_in) -> str:
		"""Persist normalized data and return the target docname.

		Must be idempotent (create-or-update keyed on the business key). Always called
		inside a transaction; the pipeline gates whether an *amendment* reaches here.
		``message_in`` is the ``EDX Message In`` document.
		"""
		raise NotImplementedError
