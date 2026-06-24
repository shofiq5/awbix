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
	frappe.logger().info(f"resolve_route inputs: {inputs}")

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
	frappe.logger().info(f"Found {len(rules)} enabled routing rules")
	for rule in rules:
		frappe.logger().info(f"Rule: {rule.get('name')} - msg_type={rule.get('message_type')}, carrier={rule.get('carrier_code')}, conn={rule.get('connection')}")

	best = None
	best_rank = None
	for rule in rules:
		specificity = 0
		matched = True
		for field in _MATCH_FIELDS:
			rule_val = (rule.get(field) or "").strip()
			if not rule_val:
				continue  # wildcard
			input_val = (inputs.get(field) or "").strip()
			if rule_val != input_val:
				matched = False
				frappe.logger().info(f"Rule {rule.get('name')} mismatch on {field}: '{rule_val}' != '{input_val}'")
				break
			specificity += 1
		if not matched:
			continue

		rank = (specificity, rule.get("priority") or 0)
		frappe.logger().info(f"Rule {rule.get('name')} matched with specificity {specificity}")
		if best_rank is None or rank > best_rank:
			best, best_rank = rule, rank

	frappe.logger().info(f"Selected rule: {best.get('name') if best else 'NONE'}")
	return best
