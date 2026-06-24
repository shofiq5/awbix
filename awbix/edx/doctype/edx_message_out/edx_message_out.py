"""EDX Message Out — the composed outbound copy + delivery ledger (strategy §4.3).

One row per outbound attempt. The controller exposes a single ``dispatch()`` action that
enqueues the full compose → verify → send cycle as a background job, so the Desk button and
the scheduler use exactly the same worker path (``dispatch_message_out``).

The send is intentionally **not** run inside the web request: a slow SMTP/SFTP/MQ handshake
would freeze the browser, and running it inline took a ``FOR UPDATE`` row lock that collided
with ``run_doc_method``'s own ``check_if_latest`` lock (→ "Lock wait timeout exceeded").
"""

import frappe
from frappe import _
from frappe.model.document import Document


class EDXMessageOut(Document):
	@frappe.whitelist()
	def dispatch(self):
		"""Mark the row Sending and enqueue the background dispatch worker.

		Returns immediately so the Desk button never blocks on transport I/O. The worker
		(``dispatch_message_out``) performs compose → verify → route → send and writes the
		terminal status (Sent / Failed / Queued-for-retry) back to this row.
		"""
		if self.delivery_status not in ("Queued", "Failed", "Sending"):
			frappe.throw(
				_("Cannot dispatch a message with status {0}").format(self.delivery_status)
			)

		# Flip to Sending in its own committed write so the button reflects progress and a
		# second click can't double-enqueue. db_set commits without re-running validate/save.
		self.db_set("delivery_status", "Sending")

		# enqueue_after_commit: the worker must not start before the db_set above commits,
		# or it will read the stale status and bail. Frappe dedupes identical enqueue jobs.
		frappe.enqueue(
			"awbix.edx.engine.pipeline.dispatch_message_out",
			queue="long",
			job_id=f"edx-dispatch-{self.name}",
			name=self.name,
			enqueue_after_commit=True,
		)
		return {"ok": True, "status": "Sending", "queued": True}
