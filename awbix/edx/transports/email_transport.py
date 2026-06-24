"""Self-managed Email transport (strategy D2): POP3/IMAP in, SMTP out.

Deliberately does **not** reuse Frappe's ``Email Account``. ``poll()`` only fetches and
returns raw payloads with a stable ``external_id`` (POP3 UIDL / IMAP UID) so the pipeline's
``(connection, external_id)`` + ``content_hash`` dedup handles re-polls (strategy R6).
"""

import email
import imaplib
import poplib
import smtplib
from email.header import decode_header, make_header
from email.message import EmailMessage

from awbix.edx.engine.base_transport import BaseTransport


def _decode(value: str) -> str:
	if not value:
		return ""
	try:
		return str(make_header(decode_header(value)))
	except Exception:
		return value


def _extract(msg) -> tuple[str, str, str]:
	"""Return (raw_payload, sender, subject) from a parsed email message.

	The Cargo-IMP payload is taken from the text/plain body; non-text attachments are
	ignored here (message splitting / attachment handling is a later concern, strategy R7).
	"""
	sender = _decode(msg.get("From", ""))
	subject = _decode(msg.get("Subject", ""))

	parts = []
	if msg.is_multipart():
		for part in msg.walk():
			if part.get_content_type() == "text/plain" and not part.get_filename():
				payload = part.get_payload(decode=True) or b""
				parts.append(payload.decode(part.get_content_charset() or "utf-8", "replace"))
	else:
		payload = msg.get_payload(decode=True) or b""
		parts.append(payload.decode(msg.get_content_charset() or "utf-8", "replace"))

	return "\n".join(p for p in parts if p).strip(), sender, subject


class EmailTransport(BaseTransport):
	# ----- config helpers -------------------------------------------------
	def _limit(self) -> int:
		return int(self.connection.max_messages_per_poll or 50)

	def _incoming_password(self):
		return self.connection.get_password("email_password") if self.connection.email_password else ""

	def _smtp_password(self):
		return self.connection.get_password("smtp_password") if self.connection.smtp_password else ""

	# ----- inbound --------------------------------------------------------
	def _connect_pop3(self):
		c = self.connection
		port = int(c.email_port or (995 if c.use_ssl else 110))
		box = poplib.POP3_SSL(c.email_host, port) if c.use_ssl else poplib.POP3(c.email_host, port)
		box.user(c.email_user)
		box.pass_(self._incoming_password())
		return box

	def _connect_imap(self):
		c = self.connection
		port = int(c.email_port or (993 if c.use_ssl else 143))
		box = imaplib.IMAP4_SSL(c.email_host, port) if c.use_ssl else imaplib.IMAP4(c.email_host, port)
		box.login(c.email_user, self._incoming_password())
		return box

	def _poll_pop3(self) -> list[dict]:
		box = self._connect_pop3()
		out = []
		try:
			uidls = box.uidl()[1]  # list of b"<index> <uidl>"
			for entry in uidls[: self._limit()]:
				idx, uidl = entry.decode().split(maxsplit=1)
				raw_bytes = b"\n".join(box.retr(int(idx))[1])
				msg = email.message_from_bytes(raw_bytes)
				raw, sender, subject = _extract(msg)
				out.append({"raw": raw, "sender": sender, "subject": subject, "external_id": uidl})
		finally:
			box.quit()
		return out

	def _poll_imap(self) -> list[dict]:
		box = self._connect_imap()
		out = []
		try:
			box.select(self.connection.mailbox or "INBOX")
			typ, data = box.search(None, "UNSEEN")
			if typ != "OK":
				return out
			ids = data[0].split()[: self._limit()]
			for num in ids:
				typ, fetched = box.fetch(num, "(UID RFC822)")
				if typ != "OK" or not fetched or not fetched[0]:
					continue
				meta, raw_bytes = fetched[0]
				uid = _imap_uid(meta) or num.decode()
				msg = email.message_from_bytes(raw_bytes)
				raw, sender, subject = _extract(msg)
				out.append({"raw": raw, "sender": sender, "subject": subject, "external_id": uid})
		finally:
			try:
				box.close()
			except Exception:
				pass
			box.logout()
		return out

	def poll(self) -> list[dict]:
		if (self.connection.incoming_protocol or "IMAP").upper() == "POP3":
			return self._poll_pop3()
		return self._poll_imap()

	# ----- outbound -------------------------------------------------------
	def send(self, raw: str, meta: dict) -> dict:
		c = self.connection
		meta = meta or {}
		msg = EmailMessage()
		msg["From"] = meta.get("from") or c.smtp_user or f"edx@{c.smtp_host or 'localhost'}"
		msg["To"] = meta.get("to")
		msg["Subject"] = meta.get("subject") or ""
		msg.set_content(raw or "")

		port = int(c.smtp_port or (465 if not c.smtp_tls else 587))
		if c.smtp_tls:
			server = smtplib.SMTP(c.smtp_host, port)
			server.starttls()
		else:
			server = smtplib.SMTP_SSL(c.smtp_host, port)
		try:
			if c.smtp_user:
				server.login(c.smtp_user, self._smtp_password())
			server.send_message(msg)
		finally:
			server.quit()
		return {"ok": True, "external_id": msg.get("Message-ID"), "response": "sent"}

	# ----- test -----------------------------------------------------------
	def test(self, direction: str = "Inbound") -> dict:
		try:
			if direction == "Outbound":
				port = int(self.connection.smtp_port or (587 if self.connection.smtp_tls else 465))
				if self.connection.smtp_tls:
					server = smtplib.SMTP(self.connection.smtp_host, port)
					server.starttls()
				else:
					server = smtplib.SMTP_SSL(self.connection.smtp_host, port)
				try:
					if self.connection.smtp_user:
						server.login(self.connection.smtp_user, self._smtp_password())
					server.noop()
				finally:
					server.quit()
				return {"ok": True, "message": f"SMTP login OK ({self.connection.smtp_host})"}

			if (self.connection.incoming_protocol or "IMAP").upper() == "POP3":
				box = self._connect_pop3()
				try:
					count = len(box.list()[1])
				finally:
					box.quit()
				return {"ok": True, "message": f"POP3 login OK, {count} message(s)"}

			box = self._connect_imap()
			try:
				box.select(self.connection.mailbox or "INBOX")
			finally:
				box.logout()
			return {"ok": True, "message": f"IMAP login OK ({self.connection.mailbox or 'INBOX'})"}
		except Exception as e:
			return {"ok": False, "message": str(e)}


def _imap_uid(meta) -> str | None:
	"""Pull the UID out of an IMAP FETCH response header like b'1 (UID 42 RFC822 {…}'."""
	try:
		text = meta.decode() if isinstance(meta, bytes) else str(meta)
		marker = "UID "
		if marker in text:
			return text.split(marker, 1)[1].split()[0]
	except Exception:
		pass
	return None
