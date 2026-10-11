# CampusFlow

A robust, command-line technical helpdesk application designed for **Learn2Earn campus staff** to log, prioritize, assign, and track IT support requests. 

This repository represents the output of a **6-Hour/Weekend long AI-Native Engineering Sprint** focused on deliberate learning, comprehensive test automation, and professional peer-review workflows.

---


## The Problem

campusflow is a cli system that aims to solve the problem by which Learn2Earn campus staff who receives technical support requests experience technical issues like: Wi-Fi outages, faulty laptops, broken development environments, and platforms inaccessibility. More so, Informal reports get lost. thus the essence of Campusflow, it is a Python command-line ticket manager that records problems, prioritizes work, assigns responsibility, and tracks progress.


## Team

- Agene Okoh - Engineer A: tickets, validation, priority
- Eyung Emmanuel - Engineer B: assign, workflow, queue, reports

---

## Running it

Requires Python 3.8+. No third-party packages, so there is nothing to install.

```
python3 main.py
```

The CLI reads from and writes to `data/tickets.json`, which is created on first save.

> `main.py` is the one file both engineers share (design decisions §8). It is merged last, after the feature branches land, so the menu dispatches against code that is already on `main`. See **Known limitations** for the current state.

## Running the tests

```
python3 -m unittest discover -s tests -v
```

107 tests across four test files once all feature branches are integrated on `main`:

| File | Covers | Tests |
|---|---|---|
| `tests/test_tickets.py` | F1 create, validation, priority engine | 19 |
| `tests/test_workflow.py` | F3 assign, F4 status transitions, reopen | 29 |
| `tests/test_reports.py` | F5 work queue, F6 report | 19 |
| `tests/test_storage.py` | F7 persistence round-trip, normalization, corrupt data handling | 40 |

## Project structure

```
campusflow/
  errors.py     CorruptDataError — a leaf module, imports nothing from the project
  tickets.py    validate_ticket_input, calculate_priority, create_ticket
  workflow.py   assign_ticket, change_status, reopen_ticket
  reports.py    work_queue, build_report
  storage.py    load_tickets, save_tickets
main.py         CLI menu — one dispatch call per feature, no business logic
tests/
docs/
  design-decisions.md   the frozen contract between the two engineers
  ai-learning-log.md    AI-assisted learning entries per engineer
data/tickets.json       the store (git-ignored)
```

## Features

| | Feature | Owner | Where |
|---|---|---|---|
| F1 | Create a ticket | A | `tickets.py` |
| F2 | List and view tickets | shared | `main.py` |
| F3 | Assign a ticket | B | `workflow.py` |
| F4 | Change status, reopen | B | `workflow.py` |
| F5 | Work queue | B | `reports.py` |
| F6 | Reports | B | `reports.py` |
| F7 | Persistence | A | `storage.py` |

## How the pieces fit together

The two modules that everything else depends on are the two that are easiest to get wrong, so both are worth stating plainly.

**Priority is computed once, at creation.** `create_ticket` calls `calculate_priority` and writes the result into the ticket's `priority` field. Nothing downstream re-derives it — `work_queue` reads `ticket["priority"]` and sorts on it. One source of truth, so a rule change cannot leave tickets ranked under an old rule.

**Tickets are validated at the boundary, then trusted inside.** `load_tickets` is the only place that normalizes. A ticket with an unknown urgency (`"urgent"`) raises `CorruptDataError` there rather than being silently defaulted. Inside the program, `work_queue` treats an unrecognised priority as a broken invariant and lets the `KeyError` surface, instead of quietly ranking the ticket last.

**Return shapes follow design decisions §3.** Mutating operations return `(ok, payload)`, where a `False` in slot one means the payload is a message fit to print. The two pure read-only projections, `work_queue` and `build_report`, return their data directly — nothing user-fixable can fail, so a flag nobody checks would be ceremony.

## Design decisions

The contract both engineers agreed to before writing code is in [`docs/design-decisions.md`](docs/design-decisions.md): error handling, the normalization contract, return shapes, the mutation model, frozen signatures, the three legal status transitions, queue ordering, module ownership, branch naming, the priority rules, and the learning-log protocol.

## Known limitations

These are stated rather than hidden, because a reviewer should not have to discover them.

- **`main.py` is not merged yet.** The feature modules are currently driven through their tests and will be integrated into the CLI menu after feature PR merges.
- **`workflow.py` trusts validated data.** It operates on tickets that `load_tickets` has already normalized and validated at the system boundary.
- **`change_status` rejects `resolved -> open`.** §5 lists that as one of exactly three legal edges, but the code reaches it only through `reopen_ticket`. The document itself argues for the split — the call site should say what the user meant — so this is intent, not drift, and it is asserted in `tests/test_workflow.py`.
- **`create_ticket` trusts `"id"` key on existing tickets.** Hand-built caller dicts missing `"id"` can raise `KeyError`, but tickets loaded via `load_tickets` are guaranteed to have valid IDs.
- **No CI.** The suite is run by hand, per the Fellows' Guide §4.5 detached-checkout procedure, and the output is recorded in the PRs.

## Pull requests

| PR | Branch | Closes |
|---|---|---|
| [#6](https://github.com/asobuilds/campusflow-table-5/pull/6) | `feat/4-queue-reports` | F5 work queue |
| [#7](https://github.com/asobuilds/campusflow-table-5/pull/7) | `feat/2-assign-workflow` | F3 + F4 workflow |
| [#8](https://github.com/asobuilds/campusflow-table-5/pull/8) | `feat/5-reports` | F6 reports, stacked on #6 |
| [#9](https://github.com/asobuilds/campusflow-table-5/pull/9) | `feat/1-ticket-creation` | F1 create + priority + F7 persistence (merged) |

Every PR was reviewed by the other engineer from a detached checkout, and approved by someone other than its author — Fellows' Guide §4.5.

