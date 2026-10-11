# CampusFlow

A command-line technical helpdesk ticket manager for Learn2Earn campus staff.
Logs, prioritizes, assigns, and tracks IT support requests (Wi-Fi outages,
faulty laptops, broken dev environments, inaccessible platforms) that would
otherwise get lost in informal reports.

Built as a two-person AI-Native Engineering Sprint. Python standard library
only — no frameworks, no database, no API keys.

## The Problem

Informal reports of campus technical issues go missing. There is no shared
record of what broke, how urgent it is, who owns it, and whether it is fixed.
CampusFlow fixes that with a small, dependable CLI backed by a JSON file.

## Team

- **Agene Okoh** — Engineer A: ticket creation, validation, priority engine, storage
- **Eyung Emmanuel** — Engineer B: assignment, workflow, work queue, reports

## Requirements

- Python 3.10 or newer (uses modern type-hint syntax in docstrings)
- No third-party packages required

## Setup

```bash
git clone https://github.com/asobuilds/campusflow-table-5.git
cd campusflow-table-5

Running the app
bash
python3 main.py

Running the tests
bash
python3 -m unittest discover -s tests -v
The test suite covers:

Ticket creation with automatic ID generation (T001, T002, ...)

Input validation (blank title, affected_users rejecting 0, 2.5,
True, None, []; case-insensitive category and urgency)

Priority calculation with all four rules and their boundaries

JSON persistence round-trip

Corrupt-data detection (malformed JSON, unknown values, duplicate IDs)

Assignment and status workflow (Engineer B)

Work queue ordering (Engineer B)

Reports (Engineer B)

Priority rules
Priority is computed by ordinary Python logic — not AI. Rules are checked in
order; the first match wins:

Rule	Condition	Result
1	urgency == "high" AND affected_users >= 10	critical
2	urgency == "high" OR affected_users >= 10	high
3	urgency == "medium" OR affected_users >= 3	medium
4	(everything else)	low
Status workflow
Three legal transitions:

open → in_progress (only if the ticket is assigned)

in_progress → resolved

resolved → open (reopen; preserves assigned_to)

open → resolved directly is rejected — the ticket must pass through
in_progress. in_progress → open is rejected — reopen is only from resolved.

Storage
Tickets are saved to data/tickets.json (git-ignored). The file is created on
first save. Starting fresh is simply deleting it:

bash
rm data/tickets.json
A missing or empty file loads as an empty ticket list (fresh start).
A malformed file raises CorruptDataError — the app refuses to run
rather than silently erasing your tickets.

Architecture
text
campusflow/
├── __init__.py         # package marker
├── errors.py           # CorruptDataError (leaf module)
├── tickets.py          # validate_ticket_input, calculate_priority, create_ticket
├── storage.py          # load_tickets, save_tickets
├── workflow.py         # assign_ticket, change_status, reopen_ticket   (B)
└── reports.py          # work_queue, build_report                       (B)

tests/
├── test_tickets.py     # 19 tests   (A)
├── test_storage.py     # 38 tests   (B)
├── test_workflow.py    # 29 tests   (B)
└── test_reports.py     #  9 tests   (B)

docs/
├── design-decisions.md # agreed function contracts and rules
└── ai-learning-log.md  # per-fellow AI interaction records
Design decisions
The full design doc lives at docs/design-decisions.md. It records:

The (ok, payload) error contract

The normalization contract (single source of truth for "what valid input is")

Function signatures (frozen)

Queue ordering rules

Module ownership and merge order

Known limitations
No GUI — CLI only by design for the sprint.

main.py (the interactive menu) is on Engineer B's branch, pending merge.

create_ticket trusts the id key of tickets it receives; load_tickets
enforces this, so the path is only reachable from hand-built dicts.

Priority is not repaired on load if a hand-edited file disagrees with the
rule table — the stored value wins (single source of truth; see §7 of the
design doc).

Pull requests
Engineer A: PR #9 — ticket creation, validation, priority, storage

Engineer B: PR #6, PR #7, PR #8
