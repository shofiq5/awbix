# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Module Overview

The **Project** module is a lightweight project-management tool for tracking AWBix's own
development. It combines manual task tracking with two optional automations:

1. A **deterministic TODO scanner** that turns `TODO`/`FIXME`/`HACK` markers in the
   awbix source tree into tracked tasks (no AI, no network).
2. A **provider-agnostic AI layer** that can propose tasks and assess whether a tracked
   task looks done. The AI is *assistive, not authoritative* — it only ever moves a task
   to `Needs Review`; a human confirms `Done`.

The AI layer is fully optional. With it disabled, the scanner and completion detection
still work via the deterministic path.

## DocTypes

| DocType | Kind | Purpose |
|---|---|---|
| `Project` | Master | Container: name, status, owner, schedule, description |
| `Project Task` | Master | The unit of work (auto-named `TASK-#####`) |
| `Project Code Reference` | Child | File path + line + marker + snippet, attached to a task |
| `Project AI Settings` | Single | Provider config: enable, provider, model, base URL, API key, limits |

### Project Task status flow

```
Open / In Progress  --(AI or deterministic: marker gone)-->  Needs Review  --(human)-->  Done
```

`source` records provenance: `Manual`, `TODO Scan`, or `AI Suggestion`.

## Key Files

- `todo_scanner.py` — walks the awbix app tree (scope = this app only), returns
  `TodoHit`s, and `sync_tasks()` creates tasks idempotently (dedup by
  `file_path:line:marker`).
- `ai_provider.py` — `AIProvider` ABC + `AnthropicProvider`, `OpenAIProvider`
  (also serves `Custom` OpenAI-compatible endpoints), and `NullProvider` (AI off).
  `get_provider(settings)` is the factory. Network calls are lazy and live only here.
- `completion.py` — repo-state-only completion detection. `deterministic_verdict()`
  checks whether the marker is still present; `assess_task()` adds AI refinement when
  enabled; `detect_completed_tasks()` is the daily scheduler entrypoint.
- `commands.py` — `project-scan-todos` and `project-detect-completed` bench commands
  (aggregated into the app-level `awbix/commands.py`).

## Configuration & Secrets

`Project AI Settings` resolves credentials by precedence:
**DocType field → `site_config.json` → environment variable**
(`ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `PROJECT_AI_API_KEY`). The API key is a
Frappe `Password` field (encrypted at rest) and must never be logged. Sending source
snippets to an external API only happens when the AI layer is explicitly enabled.

## Commands

```bash
# Create tasks from TODO/FIXME/HACK markers
bench --site <site> project-scan-todos [--project <name>]

# Re-check active tasks; move likely-done ones to Needs Review
bench --site <site> project-detect-completed
```

A `daily` scheduler event runs `detect_completed_tasks` automatically.

## Testing

```bash
bench run-tests --module Project
```

Tests never hit the network: the AI provider is mocked (`requests.post` patched, or
`NullProvider`/recorder subclasses used). Scanner/completion tests run against a
temp dir by monkeypatching `todo_scanner.app_root`.

## Conventions

Follows the AWBix DocType pattern (one folder per DocType with `.json` / `.py` /
`__init__.py`; logic in the `Document` subclass; validation via `validate()` +
`frappe.throw()`). Python 3.10+, tabs, double quotes, 110-char lines, ruff-clean.
