"""Completion detection for Project Tasks (repo-state-only).

Day-one signal source is the working tree only — no git history, no GitHub. A scan-
sourced task is considered *likely done* when its tracked TODO marker no longer exists
at the referenced location. The AI layer, when enabled, refines the verdict with
reasoning; when disabled, the deterministic check stands on its own.

Likely-done tasks are moved to ``Needs Review`` (never auto-closed) so a human
confirms before the task becomes ``Done``.
"""

from __future__ import annotations

import os

import frappe

from awbix.project import todo_scanner
from awbix.project.ai_provider import CompletionVerdict, NullProvider, get_provider

# Statuses we consider "still active" and therefore worth re-checking.
ACTIVE_STATUSES = ("Open", "In Progress")


def marker_still_present(file_path: str, line_number: int | None, marker: str) -> bool:
	"""Return True if ``marker`` still appears at/near the referenced location.

	We check the exact line first, then a small window around it so a few lines of
	drift (edits above the marker) don't produce false "done" verdicts.
	"""
	abs_path = os.path.join(todo_scanner.app_root(), file_path)
	try:
		with open(abs_path, encoding="utf-8") as fh:
			lines = fh.readlines()
	except (OSError, UnicodeDecodeError):
		return False  # file gone/unreadable -> marker no longer present

	needle = marker.upper()
	if line_number and 1 <= line_number <= len(lines):
		if needle in lines[line_number - 1].upper():
			return True
		lo = max(0, line_number - 4)
		hi = min(len(lines), line_number + 3)
		return any(needle in line.upper() for line in lines[lo:hi])
	return any(needle in line.upper() for line in lines)


def deterministic_verdict(task) -> CompletionVerdict:
	"""Repo-state-only verdict, no AI. Done iff the tracked marker is gone."""
	ref = task.primary_reference()
	if not ref:
		return CompletionVerdict(
			done=False, confidence=0.0, reasoning="No code reference to check.", uncertain=True
		)

	present = marker_still_present(ref.file_path, ref.line_number, ref.marker or "TODO")
	if present:
		return CompletionVerdict(
			done=False,
			confidence=0.9,
			reasoning=f"{ref.marker} still present at {ref.file_path}:{ref.line_number}.",
		)
	return CompletionVerdict(
		done=True,
		confidence=0.8,
		reasoning=f"{ref.marker} no longer found at {ref.file_path}:{ref.line_number}.",
	)


def assess_task(task) -> CompletionVerdict:
	"""Combine the deterministic check with optional AI refinement."""
	verdict = deterministic_verdict(task)

	provider = get_provider()
	if isinstance(provider, NullProvider):
		return verdict

	# Only spend an AI call when the cheap check already thinks it's done.
	if not verdict.done:
		return verdict

	ref = task.primary_reference()
	context = (
		f"Task: {task.title}\n"
		f"Reference: {ref.file_path}:{ref.line_number} ({ref.marker})\n"
		f"Deterministic check: marker no longer present in the working tree.\n"
		f"Decide whether this task is genuinely complete."
	)
	try:
		ai = provider.assess_completion(context)
	except Exception as exc:
		frappe.log_error(f"Project AI assess_completion failed: {exc}")
		return verdict
	return ai


def detect_completed_tasks() -> dict:
	"""Scheduler entrypoint: re-check active scan-sourced tasks.

	Moves likely-done tasks to ``Needs Review`` with the verdict recorded. Returns a
	summary dict for logging/tests.
	"""
	tasks = frappe.get_all(
		"Project Task",
		filters={"status": ["in", ACTIVE_STATUSES], "source": ["in", ("TODO Scan", "AI Suggestion")]},
		pluck="name",
	)
	moved = []
	for name in tasks:
		task = frappe.get_doc("Project Task", name)
		verdict = assess_task(task)
		if verdict.done:
			task.status = "Needs Review"
			task.ai_confidence = round(verdict.confidence, 2)
			task.ai_reasoning = verdict.reasoning[:240]
			task.save()
			moved.append(name)
	frappe.db.commit()
	return {"checked": len(tasks), "moved_to_review": moved}
