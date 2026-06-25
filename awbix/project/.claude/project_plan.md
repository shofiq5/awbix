# AWBix Project Management Tool — Build Prompt

> Paste this prompt to an AI assistant (or use it yourself as a spec) to design and
> implement a project management tool inside the AWBix Frappe app.

---

## Role

Act as a **systems architect and senior Frappe developer**. You write idiomatic
Frappe Framework v15 code, favor simple conventional solutions over clever ones, and
explain trade-offs before introducing complexity.

## Goal

Build a **simple but powerful project management tool** for tracking AWBix's own
development. It must be lightweight enough for a small team to adopt immediately, while
supporting an **optional AI layer** that:

1. **Identifies pending TODO tasks** — scans the codebase (and optionally commits,
   issues, and notes) to surface `TODO`/`FIXME`/`HACK` markers and unfinished work,
   then proposes them as tracked tasks.
2. **Detects completed tasks** — infers when a tracked task is likely done (e.g. the
   referenced TODO was removed, a linked commit/PR merged, tests added) and flags it for
   review before closing.

The AI layer is **assistive, not authoritative**: it proposes, a human confirms.

## Constraints

- **Framework:** Frappe Framework v15 custom app (`awbix`), new module: **Project**.
- **Conventions:** follow the existing AWBix DocType pattern — one folder per DocType
  under `awbix/project/doctype/<name>/` with `.json`, `.py`, `__init__.py`. Business
  logic lives in the `Document` subclass; validation via `validate()` and
  `frappe.throw()`.
- **Code style:** Python 3.10+, tabs, double quotes, 110-char lines, ruff-clean
  (`UP`, `B`, `RUF` rules). JS/SCSS via prettier + eslint.
- **No external services required** for the core tool. The AI layer should be a
  **pluggable, optional** component (degrade gracefully when disabled or offline).
- **AI provider is configurable.** The user must be able to choose which API powers the
  AI layer — **Claude (Anthropic)**, **ChatGPT (OpenAI)**, or any other compatible
  provider — and supply their own credentials. No provider is hard-coded; the choice is
  a runtime setting, not a code change.

## Deliverables

1. **Data model** — propose DocTypes and their fields. At minimum:
   - `Project` (master): name, description, status, owner, dates.
   - `Project Task`: title, description, status (`Open` / `In Progress` /
     `Needs Review` / `Done` / `Cancelled`), priority, assignee, project link,
     source reference (file path + line, or commit/PR), AI confidence, due date.
   - Consider `Task Comment` / activity log and a `Code Reference` link for traceability.
   Show the field tables and explain each choice.

2. **AI integration design** — a **provider-agnostic** interface (e.g. `ai_provider.py`)
   with two operations:
   - `discover_todos(scope) -> list[ProposedTask]`
   - `assess_completion(task) -> CompletionVerdict` (done / not done / uncertain +
     reasoning).
   Define an abstract base (e.g. `AIProvider`) with concrete subclasses such as
   `AnthropicProvider`, `OpenAIProvider`, and a `NullProvider` (AI disabled). Selection
   is by config, resolved through a small factory. Describe inputs (diffs, file contents,
   task context), prompt structure, how results map to DocType records, rate/cost
   controls, and how to mock the provider in tests.

3. **Provider configuration** — a Frappe **Single DocType** (e.g. `Project AI Settings`)
   that lets a user, without touching code:
   - **enable/disable** the AI layer;
   - **choose the provider** (`Claude (Anthropic)` / `ChatGPT (OpenAI)` / `Custom`);
   - set the **model name**, **API base URL** (for OpenAI-compatible/self-hosted
     endpoints), **API key** (stored as a Frappe `Password` field, never logged),
     and basic limits (max tokens, request timeout, monthly budget cap).
   Suggest sensible per-provider model defaults (e.g. `claude-opus-4-8` /
   `claude-haiku-4-5-20251001` for Claude). Include a **"Test connection"** action that
   validates the key/endpoint without running a full scan. Document precedence: explicit
   DocType setting → `site_config.json` → environment variable.

4. **TODO scanner** — a deterministic, non-AI scanner that walks the repo for
   `TODO`/`FIXME`/`HACK` (configurable patterns), with the AI step as an optional
   enrichment on top. Make the scanner usable as a `bench` command and/or scheduled job.

5. **Workflow** — how a proposed task moves from AI suggestion → human review →
   tracked task → `Needs Review` (AI thinks it's done) → human-confirmed `Done`.
   Include the Frappe hooks/scheduler events involved.

6. **UI** — a Kanban or list view for tasks plus a "Review AI suggestions" inbox.
   Keep it to standard Frappe list/board/workspace where possible; only add custom JS
   where it earns its keep.

7. **Testing** — `FrappeTestCase` tests for the data model and workflow, with the AI
   provider mocked. No network calls in tests. Include at least one test per provider
   subclass that asserts request shaping without hitting the network.

## Working method

- Start with the **smallest version that delivers value** (manual task tracking +
  deterministic TODO scanner). Add the AI layer as a clearly separable second phase.
- Before writing code, present: (a) the DocType field tables, (b) the module/file
  layout, and (c) the AI interface signature. Pause for confirmation.
- Then implement incrementally, running `ruff check .`, `ruff format .`, and the
  relevant `bench run-tests` after each step.
- Call out anything that adds operational cost, external dependencies, or security
  surface (especially anything that sends code to an external API).

## Open questions to resolve first

1. Scope of the TODO scan — this app only, or the whole bench/multiple apps?
2. Source signals for completion detection — repo state only, or also Git history /
   GitHub PRs / CI status?
3. Which providers must ship on day one (Claude, OpenAI, both, plus a custom
   OpenAI-compatible endpoint)? Where does each API key live, and is sending source
   snippets to an external API acceptable for this repo? If not, design for a
   local/offline fallback.
4. Single-team tool or multi-user with Frappe role-based permissions?
