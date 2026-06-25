"""Deterministic TODO scanner for the AWBix app.

Walks the awbix app source tree for TODO/FIXME/HACK markers and turns them into
``Project Task`` records (source = "TODO Scan"). This layer uses no AI and no
network; the AI layer (``ai_provider``) is an optional enrichment on top.

Scope is the awbix app only (resolved from this module's location), per the project
plan's day-one decision.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

import frappe

# Configurable marker patterns. A line matches if it contains one of these markers
# as a word, typically inside a comment. We keep this deliberately simple and
# language-agnostic rather than parsing each file's comment syntax.
DEFAULT_MARKERS = ("TODO", "FIXME", "HACK")

# Directories we never descend into.
SKIP_DIRS = frozenset(
	{
		".git",
		"node_modules",
		"__pycache__",
		"dist",
		"public",
		".claude",
	}
)

# Only scan source-ish text files.
SCAN_EXTENSIONS = frozenset({".py", ".js", ".ts", ".scss", ".css", ".md", ".json", ".html"})


@dataclass(frozen=True)
class TodoHit:
	"""A single marker occurrence found in the source tree."""

	file_path: str  # relative to the app root
	line_number: int
	marker: str
	snippet: str

	def signature(self) -> str:
		"""Stable identity used to deduplicate against existing tasks."""
		return f"{self.file_path}:{self.line_number}:{self.marker}"


@dataclass
class ScanResult:
	hits: list[TodoHit] = field(default_factory=list)
	created_task_names: list[str] = field(default_factory=list)
	skipped_existing: int = 0


def app_root() -> str:
	"""Absolute path to the awbix app root (the dir containing ``awbix/``)."""
	# This file lives at <root>/awbix/project/todo_scanner.py
	here = os.path.dirname(os.path.abspath(__file__))
	return os.path.dirname(os.path.dirname(here))


def _build_pattern(markers: tuple[str, ...]) -> re.Pattern[str]:
	alternation = "|".join(re.escape(m) for m in markers)
	return re.compile(rf"\b({alternation})\b", re.IGNORECASE)


def scan(markers: tuple[str, ...] = DEFAULT_MARKERS, root: str | None = None) -> list[TodoHit]:
	"""Walk the app tree and return every marker hit. Pure, no DB writes."""
	root = root or app_root()
	pattern = _build_pattern(markers)
	hits: list[TodoHit] = []

	for dirpath, dirnames, filenames in os.walk(root):
		dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
		for filename in filenames:
			if os.path.splitext(filename)[1] not in SCAN_EXTENSIONS:
				continue
			abs_path = os.path.join(dirpath, filename)
			rel_path = os.path.relpath(abs_path, root).replace(os.sep, "/")
			hits.extend(_scan_file(abs_path, rel_path, pattern))
	return hits


def _scan_file(abs_path: str, rel_path: str, pattern: re.Pattern[str]) -> list[TodoHit]:
	hits: list[TodoHit] = []
	try:
		with open(abs_path, encoding="utf-8") as fh:
			for line_number, line in enumerate(fh, start=1):
				match = pattern.search(line)
				if match:
					hits.append(
						TodoHit(
							file_path=rel_path,
							line_number=line_number,
							marker=match.group(1).upper(),
							snippet=line.strip()[:240],
						)
					)
	except (OSError, UnicodeDecodeError):
		# Unreadable / binary file — skip silently; scanning is best-effort.
		return []
	return hits


def _existing_signatures() -> set[str]:
	"""Signatures of scan-sourced tasks that already exist (any status).

	Built from each task's primary code reference so re-running the scan does not
	create duplicates.
	"""
	rows = frappe.get_all(
		"Project Code Reference",
		filters={"parenttype": "Project Task"},
		fields=["file_path", "line_number", "marker"],
	)
	return {f"{r.file_path}:{r.line_number}:{r.marker}" for r in rows}


def sync_tasks(markers: tuple[str, ...] = DEFAULT_MARKERS, project: str | None = None) -> ScanResult:
	"""Scan the tree and create a Project Task for each new marker hit.

	Idempotent: hits whose signature already exists on a task are skipped.
	"""
	result = ScanResult(hits=scan(markers))
	existing = _existing_signatures()

	for hit in result.hits:
		if hit.signature() in existing:
			result.skipped_existing += 1
			continue
		task = frappe.new_doc("Project Task")
		task.title = _title_for(hit)
		task.status = "Open"
		task.source = "TODO Scan"
		if project:
			task.project = project
		task.append(
			"code_references",
			{
				"file_path": hit.file_path,
				"line_number": hit.line_number,
				"marker": hit.marker,
				"snippet": hit.snippet,
			},
		)
		task.insert()
		existing.add(hit.signature())
		result.created_task_names.append(task.name)

	return result


def _title_for(hit: TodoHit) -> str:
	# Strip a leading comment marker and the TODO keyword for a cleaner title.
	text = re.sub(r"^[#/*\s-]*", "", hit.snippet)
	text = re.sub(rf"\b{re.escape(hit.marker)}\b[:\s-]*", "", text, count=1, flags=re.IGNORECASE)
	text = text.strip() or f"{hit.marker} in {hit.file_path}"
	return f"[{hit.marker}] {text[:120]}"
