"""Cargo-IMP message tokenizer (shared by FWB / FHL / FNA / FMA handlers).

Cargo-IMP messages are line-oriented: the first line is the message identifier
(``FWB/16``), the second the AWB consignment detail, then a series of segments. A
segment is a header line beginning with a 2–4 letter code followed by zero or more
``/`` continuation lines. This module only *tokenizes*; field semantics live in the
per-message parser.
"""

import re

_CODE_RE = re.compile(r"^([A-Z]{2,4})")


def normalize(raw: str) -> list[str]:
	"""Normalise newlines and drop blank lines (Type-B / CRLF tolerant)."""
	text = (raw or "").replace("\r\n", "\n").replace("\r", "\n")
	return [ln.rstrip() for ln in text.split("\n") if ln.strip() != ""]


def tokenize(raw: str) -> dict:
	"""Return ``{"message_id", "awb_line", "segments": [{"code", "lines": [...]}]}``."""
	lines = normalize(raw)
	if not lines:
		return {"message_id": None, "awb_line": None, "segments": []}

	message_id = lines[0]
	awb_line = lines[1] if len(lines) > 1 else None
	segments: list[dict] = []
	current: dict | None = None
	for ln in lines[2:]:
		if ln.startswith("/"):
			if current is None:
				current = {"code": None, "lines": []}
				segments.append(current)
			current["lines"].append(ln)
		else:
			m = _CODE_RE.match(ln)
			current = {"code": m.group(1) if m else None, "lines": [ln]}
			segments.append(current)
	return {"message_id": message_id, "awb_line": awb_line, "segments": segments}


def by_code(tokens: dict, code: str) -> list[dict]:
	return [s for s in tokens["segments"] if s["code"] == code]


def first(tokens: dict, code: str) -> dict | None:
	segs = by_code(tokens, code)
	return segs[0] if segs else None


def continuation_text(segment: dict) -> list[str]:
	"""Bodies of the ``/`` continuation lines (slash stripped); header excluded."""
	return [ln[1:].strip() for ln in segment["lines"] if ln.startswith("/")]
