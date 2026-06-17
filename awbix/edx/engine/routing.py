"""Outbound routing resolution.

Selects the best ``EDX Message Routing`` rule for a message. A rule's match fields
(``message_type``, ``carrier_code``, ``origin``, ``destination``) are wildcards when blank,
so a single default rule can catch everything while specific rules override it.

The future M5 outbound dispatcher calls ``resolve_route`` to pick a connection/address;
it is added now so routing config is usable and testable on its own.
"""

import frappe

_MATCH_FIELDS = ("message_type", "carrier_code", "origin", "destination")


def resolve_route(
	message_type: str = None,
	carrier_code: str = None,
	origin: str = None,
	destination: str = None,
) -> dict | None:
	"""Return the most specific enabled routing rule matching the inputs, or ``None``.

	Specificity = number of non-blank rule fields that matched; ties broken by ``priority``
	(higher first). A rule is rejected if any of its non-blank fields differs from the input.
	"""
	inputs = {
		"message_type": message_type,
		"carrier_code": carrier_code,
		"origin": origin,
		"destination": destination,
	}

	rules = frappe.get_all(
		"EDX Message Routing",
		filters={"enabled": 1},
		fields=[
			"name",
			"message_type",
			"carrier_code",
			"origin",
			"destination",
			"address_type",
			"address",
			"connection",
			"priority",
		],
	)

	best = None
	best_rank = None
	for rule in rules:
		specificity = 0
		matched = True
		for field in _MATCH_FIELDS:
			rule_val = (rule.get(field) or "").strip()
			if not rule_val:
				continue  # wildcard
			if rule_val != (inputs.get(field) or "").strip():
				matched = False
				break
			specificity += 1
		if not matched:
			continue

		rank = (specificity, rule.get("priority") or 0)
		if best_rank is None or rank > best_rank:
			best, best_rank = rule, rank

	return best
