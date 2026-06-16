"""EDX engine exception hierarchy.

All engine-level failures derive from ``EDXError`` so callers can catch the whole
family. These are distinct from ``frappe.ValidationError`` (business validation),
which the pipeline catches separately when persisting into business DocTypes.
"""


class EDXError(Exception):
	"""Base class for all EDX engine errors."""


class EDXClassificationError(EDXError):
	"""An inbound payload could not be classified to a (message_type, version)."""


class EDXNotRegisteredError(EDXError):
	"""No enabled handler is registered for the requested (message_type, version)."""


class EDXParseError(EDXError):
	"""A parser could not turn raw text into normalized data."""


class EDXProcessError(EDXError):
	"""Normalized data could not be persisted into business DocTypes."""


class EDXComposeError(EDXError):
	"""A composer could not build an outbound message."""


class EDXTransportError(EDXError):
	"""A transport adapter failed to connect, poll, or send."""
