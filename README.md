# CampusFlow

A robust, command-line technical helpdesk application designed for **Learn2Earn campus staff** to log, prioritize, assign, and track IT support requests.

This repository represents the output of a **6-Hour AI-Native Engineering Sprint** focused on deliberate learning, comprehensive test automation, and professional peer-review workflows.

---

## The Problem

CampusFlow solves the problem where Learn2Earn campus staff receive technical support requests — such as Wi-Fi outages, faulty laptops, broken dev environments, and inaccessible platforms — that get lost in informal chat channels. CampusFlow provides a dependable Python CLI ticket manager that records issues, prioritizes work automatically, assigns responsibility, and tracks lifecycle progress.

## Team

### Current sprint (CampusFlow Next)

- **Agene Okoh** — Engineer A: validation helpers, notes module, JSON
  persistence, ticket schema extensions (`notes`, `was_reopened`).
- **Emmanuel Elaigwu** — Engineer B: search & filtering, report enhancements
  (category breakdown, resolution percentage, reopened count), CLI
  integration for the notes menus and the Engineering Understanding Check.

### Prior sprint (CampusFlow v1)

- **Agene Okoh** — Engineer A: ticket creation, validation, priority engine,
  JSON storage.
- **Eyung Emmanuel** — Engineer B: assignment, workflow, queue, reports.

The v1 work is preserved as the baseline for CampusFlow Next. The audit
snapshot for that baseline is in `docs/baseline-check.md`.

## Running It

Requires Python 3.8+ (standard library only; zero external dependencies).

```bash
python3 main.py
```

The CLI reads from and writes to `data/tickets.json`, which is automatically created on first save.

## Running the Tests

```bash
python3 -m unittest discover -s tests -v
```

119 automated unit tests across five test suites:

| File | Covers | Tests |
|---|---|---|
| `tests/test_tickets.py` | F1 create, input validation, priority calculation rules | 19 |
| `tests/test_workflow.py` | F3 assign, F4 strict status transitions, reopen | 29 |
| `tests/test_reports.py` | F5 work queue, F6 summary report | 19 |
| `tests/test_storage.py` | F7 persistence round-trip, normalization, corrupt data handling | 40 |
| `tests/test_main.py` | CLI menu handlers, single dispatch, startup error handling | 12 |

## Project Structure

```
campusflow/
  errors.py     CorruptDataError — a leaf module, imports nothing from the project
  tickets.py    validate_ticket_input, calculate_priority, create_ticket
  workflow.py   assign_ticket, change_status, reopen_ticket
  reports.py    work_queue, build_report
  storage.py    load_tickets, save_tickets
main.py         CLI menu — one dispatch call per feature, no business logic
tests/          Complete automated test suite (119 unit tests)
docs/
  design-decisions.md   the frozen contract between the two engineers
  ai-learning-log.md    AI-assisted learning entries per engineer
data/tickets.json       the store (git-ignored)
```
## CampusFlow Next — what changed

Beyond the v1 baseline:

- **Structured follow-up notes.** Every ticket carries `notes: [...]`.
  `add_note` validates author (non-blank) and message (5–300 chars), rejects
  notes on resolved tickets, and never consumes a note ID on failure. See
  §12 of `docs/design-decisions.md`.
- **`was_reopened` flag.** Set to `True` by `reopen_ticket`, sticky forever.
  Legacy tickets missing the key default to `False` on load. Used by the
  report to count ever-reopened tickets.
- **Extended reports.** Totals by status, priority, and category; unresolved
  and resolved counts; resolution percentage (guarded against zero); reopened
  count.
- **Safe JSON load.** `load_tickets` validates the full notes schema, enforces
  per-ticket note-ID uniqueness by numeric value, and preserves stored
  priorities (never re-derived). See §12.7.
- **Test suite.** 163 tests, all passing on `main`.

## Features

| | Feature | Owner | Implementation |
|---|---|---|---|
| F1 | Create a ticket | Engineer A | `campusflow/tickets.py` |
| F2 | List and view tickets | Shared | `main.py` |
| F3 | Assign a ticket | Engineer B | `campusflow/workflow.py` |
| F4 | Change status, reopen | Engineer B | `campusflow/workflow.py` |
| F5 | Work queue | Engineer B | `campusflow/reports.py` |
| F6 | Reports | Engineer B | `campusflow/reports.py` |
| F7 | Persistence | Engineer A | `campusflow/storage.py` |

## How the Pieces Fit Together

The two modules that everything else depends on are designed around clear invariants:

- **Priority is computed once, at creation.** `create_ticket` calls `calculate_priority` and writes the result into the ticket's `priority` field. Nothing downstream re-derives it — `work_queue` reads `ticket["priority"]` and sorts on it. A single source of truth prevents rule divergence across the program.
- **Tickets are validated at the boundary, then trusted inside.** `load_tickets` is the system normalizer and validator. Malformed JSON, illegal statuses, or missing keys raise `CorruptDataError` immediately at load time. Internal domain functions in `workflow.py` and `reports.py` trust the in-memory structures without defensive duplication.
- **Return shapes follow Design Decisions §3.** Mutating functions return `(ok, payload)`, where `False` indicates a user-fixable validation message fit to print. Pure read-only projections (`work_queue`, `build_report`) return raw values directly. Structural failures raise `CorruptDataError`.

## Priority Engine

Priority is computed by ordinary Python logic — not AI. Rules are checked strictly in order; the first match wins:

| Rule | Condition | Result |
|---|---|---|
| 1 | `urgency == "high" AND affected_users >= 10` | `critical` |
| 2 | `urgency == "high" OR affected_users >= 10` | `high` |
| 3 | `urgency == "medium" OR affected_users >= 3` | `medium` |
| 4 | All remaining valid tickets | `low` |

## Status Workflow

Three legal transitions with single entry points:

- `open -> in_progress` (only if the ticket is assigned)
- `in_progress -> resolved`
- `resolved -> open` (reopen; preserves `assigned_to`)

Direct `open -> resolved` and `in_progress -> open` transitions are rejected.

## Storage Contract

- Tickets are persisted as JSON in `data/tickets.json`.
- A missing or whitespace-only file returns `[]` (fresh start).
- Missing keys, duplicate IDs (by numeric value), and illegal values raise `CorruptDataError`.
- IDs are zero-padded to three digits (`"T7"` -> `"T007"`).

## Known Limitations

- **`workflow.py` trusts validated data.** It operates on tickets that `load_tickets` has already normalized and validated at the system boundary.
- **`change_status` rejects `resolved -> open`.** The contract separates this transition into `reopen_ticket` so the user's explicit intent is clear at the call site.
- **`create_ticket` trusts `"id"` key on existing tickets.** Hand-built caller dicts missing `"id"` can raise `KeyError`, but tickets loaded via `load_tickets` are guaranteed to have valid IDs.
- **No CI.** The suite is run by hand, per the Fellows' Guide §4.5 detached-checkout procedure, and the output is recorded in the PRs.

## Pull Requests

| PR | Branch | Closes / Purpose | Status |
|---|---|---|---|
| [#9](https://github.com/asobuilds/campusflow-table-5/pull/9) | `feat/1-ticket-creation` | F1 create + priority + F7 storage | Merged |
| [#7](https://github.com/asobuilds/campusflow-table-5/pull/7) | `feat/2-assign-workflow` | F3 assign + F4 workflow | Merged |
| [#6](https://github.com/asobuilds/campusflow-table-5/pull/6) | `feat/4-queue-reports` | F5 work queue | Merged |
| [#8](https://github.com/asobuilds/campusflow-table-5/pull/8) | `feat/5-reports` | F6 summary reports | Merged |
| [#10](https://github.com/asobuilds/campusflow-table-5/pull/10) | `docs/readme` | Complete documentation & run guide | Open |
| [#11](https://github.com/asobuilds/campusflow-table-5/pull/11) | `feat/cli-menu` | F2 view + `main.py` CLI menu integration | Pending Review |

Every PR was reviewed by the other engineer from a detached checkout, and approved by someone other than its author — Fellows' Guide §4.5.
