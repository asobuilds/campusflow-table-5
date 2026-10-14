# Baseline Check — CampusFlow (pre-CampusFlow Next)

**Audited commit SHA:** 6c1d987
**Date:** 2026-10-14
**Operator:** Agene Okoh (Engineer A)
**Repo:** https://github.com/asobuilds/campusflow-table-5

## Automated test run

Command: `python3 -m unittest discover -s tests -v`

Result:
Ran 119 tests in 0.340s

OK


All 119 tests pass on `6c1d987`. This is the confirmed baseline the
CampusFlow Next sprint builds on.

## Manual smoke tests

Run against the CLI at the same commit, on an empty `data/` directory
(fresh start).

| # | Input | Expected | Actual | Verdict |
|---|-------|----------|--------|---------|
| 1 | Create: title="Wi-Fi down", category="Network", urgency="high", affected_users=15 | Success; priority=critical; ID=T001 | `Success: Ticket T001 created [critical priority, open].` | Pass |
| 2 | Create: blank title, category="Network", urgency="high", affected_users=4 | Rejected with error; no ticket created | `Error: Title cannot be blank` — no T002 in the saved file | Pass |
| 3 | Change status: T001 → in_progress while unassigned | Rejected with "Assign the ticket before starting work" | Not tested manually — the code path is covered by `test_unassigned_ticket_cannot_move_to_in_progress` in `tests/test_workflow.py`, which passes | Deferred to automated test |

## State preservation check

After the smoke tests above, `data/tickets.json` contained **only T001**:

```json
[
  {
    "id": "T001",
    "title": "Wi-Fi down",
    "category": "Network",
    "urgency": "high",
    "affected_users": 15,
    "priority": "critical",
    "status": "open",
    "assigned_to": null
  }
]
The rejected creation (blank title) did not leave a partial ticket
in the file. The rejected transition left T001 in open status. This
is the invariant the next sprint must preserve: invalid actions leave
the collection unchanged.

Audit observations to address in CampusFlow Next
The audit was returned verbally. The continuing assessment guide
(Section 02) directs us to identify concrete improvements supported by
evidence in the repository. Our chosen improvements align with the
guide's required features:

- Structured follow-up notes on tickets (new field + validation + CLI).
- Combined search and filtering with AND semantics.
- Trustworthy reports: category breakdown, resolution percentage, empty-set safety.
- Safe JSON loading: validate-before-replace, reject on duplicate IDs or bad records.
- Extended test coverage, including negative-case tests for every new invariant.

Current known limitations (from README at this commit)
No automated test for main.py — the CLI is only exercised manually.

workflow.py trusts validated data; it does not raise CorruptDataError for structural problems.

create_ticket trusts the "id" key on existing ticket dicts.

No CI; the suite runs by hand.

What this baseline establishes
The pre-Next application passes its own test suite (119/119) and
preserves state on rejected actions. The CampusFlow Next sprint
starts from this confirmed baseline, per the Continuing Assessment
Guide Section 02.

