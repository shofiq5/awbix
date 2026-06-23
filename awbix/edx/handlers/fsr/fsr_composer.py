"""FSR (Flight Status Request) outbound composer.

Builds a two-line Cargo-IMP FSR message from a Shipment document:

    FSR
    {airline_prefix}-{awb_serial_number}
"""

import frappe

from awbix.edx.engine.base_composer import BaseComposer
from awbix.edx.handlers.fwb import cargoimp


class FSRComposer(BaseComposer):
	message_type = "FSR"
	version = "1"

	def compose(self, source_doc) -> str:
		d = source_doc
		self._assert_mandatory(d)
		lines = [
			"FSR",
			f"{d.get('airline_prefix')}-{d.get('awb_serial_number')}",
		]
		return cargoimp.join(lines)

	def _assert_mandatory(self, d) -> None:
		missing = []
		if not (d.get("airline_prefix") or "").strip():
			missing.append("airline prefix")
		if not (d.get("awb_serial_number") or "").strip():
			missing.append("AWB serial number")
		if missing:
			frappe.throw(
				"Cannot compose FSR for {0}: missing mandatory data - {1}".format(
					d.get("name") or "shipment", "; ".join(missing)
				)
			)
