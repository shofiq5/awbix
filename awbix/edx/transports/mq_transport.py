"""MQ transport — RabbitMQ via ``pika`` (AMQP 0-9-1).

The base interface stays broker-agnostic (strategy R10); this is the one concrete adapter.
``poll()`` drains ``queue_in`` with ``basic_get`` (ack on fetch — the pipeline then dedups
and persists), ``send()`` publishes to the exchange/routing-key (or ``queue_out``).
``pika`` is imported lazily so a host without it fails the Test cleanly.
"""

from awbix.edx.engine.base_transport import BaseTransport


class MQTransport(BaseTransport):
	def _connect(self):
		import pika

		c = self.connection
		password = c.get_password("mq_password") if c.mq_password else ""
		credentials = pika.PlainCredentials(c.mq_username or "guest", password or "guest")
		params = pika.ConnectionParameters(
			host=c.mq_host,
			port=int(c.mq_port or 5672),
			virtual_host=c.mq_vhost or "/",
			credentials=credentials,
			ssl_options=_ssl_options(c) if c.mq_use_tls else None,
		)
		return pika.BlockingConnection(params)

	def poll(self) -> list[dict]:
		c = self.connection
		if not c.queue_in:
			return []
		conn = self._connect()
		out = []
		try:
			channel = conn.channel()
			limit = int(c.max_messages_per_poll or 50)
			for _ in range(limit):
				method, props, body = channel.basic_get(queue=c.queue_in, auto_ack=True)
				if method is None:
					break
				raw = body.decode("utf-8", "replace") if isinstance(body, bytes) else str(body)
				external_id = (props.message_id if props else None) or str(method.delivery_tag)
				out.append(
					{"raw": raw, "sender": c.mq_host, "subject": c.queue_in, "external_id": external_id}
				)
		finally:
			conn.close()
		return out

	def send(self, raw: str, meta: dict) -> dict:
		import pika

		c = self.connection
		meta = meta or {}
		exchange = meta.get("exchange") or c.mq_exchange or ""
		routing_key = meta.get("routing_key") or c.mq_routing_key or c.queue_out
		conn = self._connect()
		try:
			channel = conn.channel()
			channel.basic_publish(
				exchange=exchange,
				routing_key=routing_key or "",
				body=(raw or "").encode("utf-8"),
				properties=pika.BasicProperties(
					message_id=meta.get("external_id"), delivery_mode=2  # persistent
				),
			)
		finally:
			conn.close()
		return {"ok": True, "external_id": meta.get("external_id"), "response": f"published to {routing_key}"}

	def test(self, direction: str = "Inbound") -> dict:
		c = self.connection
		try:
			conn = self._connect()
			try:
				channel = conn.channel()
				queue = c.queue_in if direction != "Outbound" else c.queue_out
				detail = "connected"
				if queue:
					res = channel.queue_declare(queue=queue, passive=True)
					detail = f"queue '{queue}' has {res.method.message_count} message(s)"
			finally:
				conn.close()
			return {"ok": True, "message": f"RabbitMQ OK, {detail}"}
		except Exception as e:
			return {"ok": False, "message": str(e)}


def _ssl_options(connection):
	import ssl

	import pika

	return pika.SSLOptions(ssl.create_default_context(), connection.mq_host)
