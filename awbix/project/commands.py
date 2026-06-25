"""Bench commands for the Project module.

Usage (from the bench root):

    bench --site <site> project-scan-todos
    bench --site <site> project-detect-completed
"""

import click
import frappe
from frappe.commands import pass_context


@click.command("project-scan-todos")
@click.option("--project", default=None, help="Attach created tasks to this Project.")
@pass_context
def scan_todos(context, project):
	"""Scan the awbix app for TODO/FIXME/HACK markers and create Project Tasks."""
	from awbix.project import todo_scanner

	site = _get_site(context)
	frappe.init(site=site)
	frappe.connect()
	try:
		result = todo_scanner.sync_tasks(project=project)
		frappe.db.commit()
		click.echo(
			f"Scanned {len(result.hits)} markers: "
			f"created {len(result.created_task_names)}, skipped {result.skipped_existing} existing."
		)
	finally:
		frappe.destroy()


@click.command("project-detect-completed")
@pass_context
def detect_completed(context):
	"""Re-check active tasks and move likely-done ones to Needs Review."""
	from awbix.project import completion

	site = _get_site(context)
	frappe.init(site=site)
	frappe.connect()
	try:
		summary = completion.detect_completed_tasks()
		click.echo(
			f"Checked {summary['checked']} tasks; moved {len(summary['moved_to_review'])} to Needs Review."
		)
	finally:
		frappe.destroy()


def _get_site(context):
	site = context.sites[0] if context.sites else None
	if not site:
		raise click.UsageError("Please specify a site with --site.")
	return site


commands = [scan_todos, detect_completed]
