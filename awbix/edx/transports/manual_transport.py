"""Manual transport — ingestion happens via API/upload, never by polling.

Exists so ``Manual`` is a first-class channel in the registry without special-casing
anywhere in the pipeline. It never polls and cannot deliver.
"""

from awbix.edx.engine.base_transport import BaseTransport


class ManualTransport(BaseTransport):
	def test(self, direction: str = "Inbound") -> dict:
		return {"ok": True, "message": "Manual channel — ingest via API/upload."}

	def poll(self) -> list[dict]:
		return []

	def send(self, raw: str, meta: dict) -> dict:
		return {"ok": False, "external_id": None, "response": "Manual channel is not deliverable."}
