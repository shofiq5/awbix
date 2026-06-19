"""FWB/16 (Air Waybill, Cargo-IMP) outbound composer.

The inverse of ``FWB16Parser``: it reads a ``Shipment`` and emits Cargo-IMP text for the
same segments the parser understands (message id, AWB consignment line, RTG routing,
SHP/CNE/AGT parties, CVD currency), so ``parse(compose(shipment))`` round-trips those
fields. ``verify`` re-parses the output through the parser as a genuine self-check.
"""

from awbix.edx.engine.base_composer import BaseComposer
from awbix.edx.handlers.fwb import cargoimp
from awbix.edx.handlers.fwb.fwb16_parser import FWB16Parser


class FWB16Composer(BaseComposer):
	message_type = "FWB"
	version = "16"

	# ------------------------------------------------------------------ compose
	def compose(self, source_doc) -> str:
		lines = ["FWB/16", self._awb_line(source_doc)]

		routing = self._routing_line(source_doc)
		if routing:
			lines.append(routing)

		for code, fieldname in (("SHP", "shipper_name"), ("CNE", "consignee_name"), ("AGT", "agent_name")):
			value = (source_doc.get(fieldname) or "").strip()
			if value:
				lines += cargoimp.segment(code, value)

		currency = (source_doc.get("currency") or "").strip()
		if currency:
			lines.append(f"CVD/{currency}//PP/NVD/NCV/XXX")

		return cargoimp.join(lines)

	def _awb_line(self, doc) -> str:
		prefix = (doc.get("airline_prefix") or "").strip()
		serial = (doc.get("awb_serial_number") or "").strip()
		origin = (doc.get("origin") or "").strip().upper()
		dest = (doc.get("destination") or "").strip().upper()
		line = f"{prefix}-{serial}{origin}{dest}"

		pieces = doc.get("number_of_pieces")
		weight = doc.get("weight")
		if pieces and weight:
			weight_code = (doc.get("weight_code") or "K").strip()
			line += f"/T{int(pieces)}{weight_code}{_num(weight)}"
		return line

	def _routing_line(self, doc) -> str:
		rows = sorted(doc.get("routing") or [], key=lambda r: r.get("sequence") or 0)
		tokens = []
		for r in rows:
			airport = (r.get("airport") or "").strip().upper()
			if not airport:
				continue
			tokens.append(airport + (r.get("carrier_code") or "").strip().upper())

		if not tokens:
			# fall back to the flat route fields
			a1 = (doc.get("to_airport1") or "").strip().upper()
			c1 = (doc.get("by_carrier1") or "").strip().upper()
			if a1:
				tokens.append(a1 + c1)
			a2 = (doc.get("to_airport2") or "").strip().upper()
			c2 = (doc.get("by_carrier2") or "").strip().upper()
			if a2:
				tokens.append(a2 + c2)

		return "RTG/" + "/".join(tokens) if tokens else ""

	# ------------------------------------------------------------------- verify
	def verify(self, raw: str) -> list[dict]:
		parser = FWB16Parser()
		return parser.validate(parser.parse(raw))


def _num(value) -> str:
	"""Render a numeric weight without a trailing ``.0`` (40.0 -> '40', 0.36 -> '0.36')."""
	f = float(value)
	return str(int(f)) if f.is_integer() else ("%g" % f)
