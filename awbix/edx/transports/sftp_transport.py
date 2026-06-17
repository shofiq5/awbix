"""SFTP transport (paramiko).

``poll()`` lists the inbound directory, downloads each file (filename = ``external_id`` so
re-listing dedups via the pipeline), and optionally archives it. ``paramiko`` is imported
lazily so a host without the lib fails the Test cleanly instead of breaking import.
"""

import io
import posixpath

from awbix.edx.engine.base_transport import BaseTransport


class SFTPTransport(BaseTransport):
	def _client(self):
		import paramiko

		c = self.connection
		transport = paramiko.Transport((c.sftp_host, int(c.sftp_port or 22)))
		key_pem = c.get_password("sftp_private_key") if c.sftp_private_key else None
		password = c.get_password("sftp_password") if c.sftp_password else None
		if key_pem:
			pkey = paramiko.RSAKey.from_private_key(io.StringIO(key_pem))
			transport.connect(username=c.sftp_username, pkey=pkey)
		else:
			transport.connect(username=c.sftp_username, password=password)
		return transport, paramiko.SFTPClient.from_transport(transport)

	def poll(self) -> list[dict]:
		c = self.connection
		transport, sftp = self._client()
		out = []
		try:
			path = c.remote_inbound_path or "."
			limit = int(c.max_messages_per_poll or 50)
			for fname in sorted(sftp.listdir(path))[:limit]:
				remote = posixpath.join(path, fname)
				try:
					attr = sftp.stat(remote)
					if not _is_file(attr):
						continue
				except OSError:
					continue
				with sftp.open(remote, "r") as fh:
					raw = fh.read().decode("utf-8", "replace")
				out.append({"raw": raw, "sender": c.sftp_host, "subject": fname, "external_id": fname})
				if c.archive_after_fetch and c.archive_path:
					sftp.rename(remote, posixpath.join(c.archive_path, fname))
		finally:
			sftp.close()
			transport.close()
		return out

	def send(self, raw: str, meta: dict) -> dict:
		c = self.connection
		meta = meta or {}
		fname = meta.get("filename") or f"{meta.get('external_id', 'message')}.txt"
		transport, sftp = self._client()
		try:
			remote = posixpath.join(c.remote_outbound_path or ".", fname)
			with sftp.open(remote, "w") as fh:
				fh.write(raw or "")
		finally:
			sftp.close()
			transport.close()
		return {"ok": True, "external_id": fname, "response": f"uploaded {fname}"}

	def test(self, direction: str = "Inbound") -> dict:
		try:
			transport, sftp = self._client()
			try:
				path = (
					self.connection.remote_outbound_path
					if direction == "Outbound"
					else self.connection.remote_inbound_path
				) or "."
				count = len(sftp.listdir(path))
			finally:
				sftp.close()
				transport.close()
			return {"ok": True, "message": f"SFTP OK, {count} entr(ies) in {path}"}
		except Exception as e:
			return {"ok": False, "message": str(e)}


def _is_file(attr) -> bool:
	import stat

	return not stat.S_ISDIR(attr.st_mode)
