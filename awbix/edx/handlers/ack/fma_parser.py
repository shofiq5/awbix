"""FMA (Acknowledgement, Cargo-IMP) inbound parser — a partner accepted our FWB.

Inbound-only (strategy D1): it never creates a Shipment, it marks the referenced one
Acknowledged and flips the matching outbound FWB to Delivered.
"""

from awbix.edx.engine.base_parser import BaseParser
from awbix.edx.handlers.ack import ack_common


class FMAParser(BaseParser):
	message_type = "FMA"
	version = "1"

	def parse(self, raw: str) -> dict:
		return ack_common.parse_ack(raw, self.message_type)

	def business_key(self, data: dict):
		return ack_common.extract_awb(data.get("received_message", ""))

	def validate(self, data: dict) -> list[dict]:
		return ack_common.validate_ack(data)

	def process(self, data: dict, message_in) -> str | None:
		key = self.business_key(data)
		target = ack_common.apply_ack(key, "Acknowledged", data.get("reason", ""))
		if target:
			ack_common.reconcile_message_out(key, "ack", data.get("reason", ""))
		return target
