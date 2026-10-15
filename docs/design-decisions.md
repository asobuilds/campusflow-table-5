# CampusFlow — Design Decisions

Agreed by Engineer A (Agene) and Engineer B (Eyung) before any code is written.
Frozen after the first review round.

## 1. Error handling

- **User errors** (things a person can fix by typing differently): functions return a tuple `(ok, payload)`.
  - `ok = True`  -> `payload` is the successful data (e.g., a ticket dictionary).
  - `ok = False` -> `payload` is a short message the CLI will print.
- **Structural errors** (broken data files, missing keys): we raise `CorruptDataError`.
  - Defined in `campusflow/errors.py`.
  - This file imports nothing from the rest of the project (it is a "leaf" module).
  - Raised from `storage.py` and `workflow.py` when the data itself is broken.

## 2. Normalization contract (CRITICAL - do not skip)

- `validate_ticket_input(title, category, urgency, affected_users)` is a PURE function.
  - No list access. No mutation. No side effects. Just data in, data out.
  - Returns `(True, (title, category, urgency, affected_users))` with values normalized, OR `(False, "error message")`.
- Normalization rules:
  - `title` is stripped of leading/trailing spaces.
  - `category` is matched case-insensitively and stored as `Network` / `Hardware` / `Software` / `Other`.
  - `urgency` is lowercased to `low` / `medium` / `high`.
  - `affected_users` is parsed from the raw value (which may be a string from `input()`).
- A blank title (after `.strip()`) -> `(False, "Title cannot be blank")`.
- Booleans are rejected FIRST in the affected_users validator: `isinstance(x, bool)` returns `(False, "affected_users must be a positive whole number")`. Reason: `True == 1` in Python; a hand-edited JSON with `"affected_users": true` must not become 1.
- `calculate_priority(urgency, affected_users)` REQUIRES ALREADY-NORMALIZED input.
  - It compares `urgency == "high"` literally, using lowercase.
- Every entry point that stores urgency MUST normalize first:
  - `create_ticket` - calls `validate_ticket_input`.
  - `storage.load_tickets` - re-normalizes each ticket after reading JSON (defensive against hand-edited files).
- `load_tickets` normalization rules:
  - Case variation of `low` / `medium` / `high` -> normalize.
  - Unknown value (e.g., `"urgent"`) OR missing key -> raise `CorruptDataError`.
  - Never pass through an unnormalized value; never default it.
- Test obligation: `urgency="High", affected_users=2` must return priority `"high"`, not `"low"`.

## 3. Return shape

- Every public function returns `(ok, payload)`.
- Slot 2 is only meaningful after checking that slot 1 is True.

### Deliberate exceptions to `(ok, payload)`

Two different kinds of exception. Do not conflate them.

- **Pure projections** - `work_queue(tickets)` returns `list[dict]` and `build_report(tickets)` returns `dict`, directly.
  - Reason: pure projections over in-memory data. Nothing user-fixable can fail. A flag nobody checks is ceremony.
- **Load-or-raise** - `load_tickets(path)` returns `list[dict]` OR raises `CorruptDataError`.
  - Reason: this is section 1's contract, not a special case. Structural failure is an exception, not a user error.
- `save_tickets(tickets, path)` returns `None`.

## 4. Mutation model

- `create_ticket(tickets, ...)` appends the new ticket dict to `tickets` AND returns `(True, new_dict)`.
- `assign_ticket(tickets, ticket_id, name)` mutates the dict in place and returns `(True, same_dict)`.
- No copies are made. `json.dump(tickets, ...)` writes the live list directly.

## 5. Function signatures (frozen)

    # tickets.py  (Engineer A)
    validate_ticket_input(title, category, urgency, affected_users) -> (ok, tuple|str)
    calculate_priority(urgency, affected_users) -> str
    create_ticket(tickets, title, category, urgency, affected_users) -> (ok, dict|str)

    # workflow.py  (Engineer B)
    assign_ticket(tickets, ticket_id, staff_name)   -> (ok, dict|str)
    change_status(tickets, ticket_id, new_status)   -> (ok, dict|str)
    reopen_ticket(tickets, ticket_id)               -> (ok, dict|str)

    # reports.py  (Engineer B)
    work_queue(tickets)    -> list[dict]
    build_report(tickets)  -> dict

    # storage.py  (Engineer A code, Engineer B tests)
    load_tickets(path)          -> list[dict]   # raises CorruptDataError
    save_tickets(tickets, path) -> None

### Status transitions (STRICT)

Exactly three legal edges:

- `open -> in_progress` (only if `assigned_to` is not None)
- `in_progress -> resolved`
- `resolved -> open` (reopen; PRESERVES `assigned_to`)

Rejected:

- `open -> resolved` (must go through `in_progress`)
- `in_progress -> open`
- Any same-state change.

Reopen preserves `assigned_to` so the reopened ticket is not trapped by the unassigned rule.

`reopen_ticket` is kept separate from `change_status` for readability: the menu call site should say what the user meant, and tests should assert on the specific operation, not on a generic status change whose legality depends on current state.

## 6. Assignment on a resolved ticket

- Rejected. `assign_ticket` on `status == "resolved"` returns `(False, "...")`.
- Justification: Section 1.4 F4 of the Fellows' Guide says "a resolved ticket may only be modified after an explicit reopen." "Modified" covers `assigned_to`.

## 7. Queue ordering

### Queue content

- Include only tickets with status `open` or `in_progress`.
- Exclude `resolved`.
- Do NOT re-derive priority in the queue. Read `ticket["priority"]`, which was written by `create_ticket`. Single source of truth.

### Ordering

- Sort by priority rank: `critical=0, high=1, medium=2, low=3`.
- Tie-break by `int(ticket["id"][1:])` - numeric, not string.
- Test obligation: `T999` must sort before `T1000`; `T002` must sort before `T010`.

## 8. Module ownership

- Engineer A (Agene): `campusflow/tickets.py`, `campusflow/storage.py` (code), `campusflow/errors.py`, `tests/test_tickets.py`.
- Engineer B (Eyung): `campusflow/workflow.py`, `campusflow/reports.py`, `tests/test_workflow.py`, `tests/test_reports.py`, `tests/test_storage.py`.
- Shared: `main.py`. Each feature's menu branch is a single dispatch call. No business logic in `main.py`.
- Merge order: whoever merges second rebases on main, reruns `python3 -m unittest discover -s tests -v`, and requests re-approval before merging.

## 9. Branch naming

Format: `feat/<issue#>-<short-description>` (lowercase, hyphens).

Examples: `feat/1-ticket-creation`, `feat/2-assign-workflow`, `feat/4-queue-reports`.

## 10. Priority engine (from the assessment guide, Section 1.3)

Check rules IN ORDER. First match wins.

1. `urgency == "high" AND affected_users >= 10` -> `"critical"`
2. `urgency == "high" OR affected_users >= 10`  -> `"high"`
3. `urgency == "medium" OR affected_users >= 3` -> `"medium"`
4. All other valid tickets -> `"low"`

## 11. AI learning log

- One shared file: `docs/ai-learning-log.md`.
- Each fellow edits ONLY their own section.
- Append at the END of your own section so the two sections grow apart, not into each other.
- If we collide at merge time, follow section 4.6 of the Fellows' Guide: inspect the markers, keep both, resolve on the branch, rerun tests.

### `load_tickets` decision table

`load_tickets` is a **normalizer**, not a strict type validator. Rule:
accept anything that can be normalized to what `create_ticket` writes;
reject anything that cannot.

Missing file or empty file -> return `[]` (fresh start, not an error).
Malformed JSON (syntax) -> raise `CorruptDataError`.
Top-level JSON not a list -> raise `CorruptDataError`.

Per ticket dict:

| Field | Accept (normalize) | Reject (raise `CorruptDataError`) |
|-------|--------------------|-----------------------------------|
| `id` | `^T\d+$`; normalize to `f"T{int(id[1:]):03d}"`. So `"T7"` -> `"T007"`. Uniqueness on `int(id[1:])`, not on the string. | wrong prefix, no digits, lowercase `t`, duplicates by numeric value (`"T7"` and `"T007"` collide), missing |
| `title` | non-empty string after `.strip()` | `""`, `"   "`, non-string, missing |
| `category` | case-insensitive match of `network`/`hardware`/`software`/`other`; store canonical (`Network`) | unknown value, non-string, missing |
| `urgency` | case-insensitive match of `low`/`medium`/`high`; store lowercase | unknown value, non-string, missing |
| `affected_users` | positive int, or string that parses to positive int | `0`, negative, `2.5`, `True`, `None`, `[]`, `""`, `"seven"`, missing |
| `priority` | case-insensitive match of `critical`/`high`/`medium`/`low`; store lowercase; **trusted, never recomputed** | unknown value, non-string, missing |
| `status` | case-insensitive match of `open`/`in_progress`/`resolved`; store lowercase | unknown value, non-string, missing |
| `assigned_to` | `None`, or non-empty string after `.strip()` | `""`, `"   "`, non-string, missing key |

Implementation note: `load_tickets` reuses `validate_ticket_input` for
`title`, `category`, `urgency`, `affected_users` — so validation logic
has a single home shared between `create_ticket` and `load_tickets`.
The extra checks for `id`, `priority`, `status`, `assigned_to` live in
`load_tickets` (create_ticket sets them, load_tickets validates them).

Uniqueness of `id` across the loaded file is enforced on `int(id[1:])`.

## 12. CampusFlow Next — Structured follow-up notes

Added in the CampusFlow Next sprint. Extends §1–§11 without changing them.

### 12.1 Note schema

Every ticket carries a `notes` field — a list of note dicts. Newly created
tickets start with `notes: []`.

A note is a dict with exactly three keys:

```python
{
    "note_id": "N001",
    "author":  "Mentor A",
    "message": "Wi-Fi router reboot attempted",
}

note_id — string matching ^N\d+$. Per-ticket sequence. First note on a
ticket is N001, second is N002. Each ticket has its own sequence —
T002's first note is also N001. A note is identified by the pair
(ticket_id, note_id).

author — non-empty string after .strip().

message — string of length 5–300 inclusive after .strip().

12.2 Function contracts
python
# notes.py  (Engineer A)
add_note(tickets, ticket_id, author, message)      -> (True, note_dict) | (False, message_str)
get_ticket_notes(tickets, ticket_id)               -> (True, list[dict]) | (False, message_str)
next_note_id(ticket)                               -> str
12.3 add_note — validation and behavior
Returns (True, note) on success, (False, message) on any user-fixable failure.

Checks in this order — return the FIRST failure:

ticket_id not found → (False, "No ticket with ID {ticket_id}.")

ticket["status"] == "resolved" → (False, "Cannot add a note to a resolved ticket; reopen it first.")

author not a string, or blank after .strip() → (False, "Author cannot be blank.")

message not a string, or length < 5 after .strip() → (False, "Message must be at least 5 characters.")

message length > 300 after .strip() → (False, "Message must be at most 300 characters.")

On success:

Compute new_id = next_note_id(ticket).

Build the note dict.

Append it to ticket["notes"].

Return (True, note).

ID-continuity invariant: a failed add_note must NOT modify
ticket["notes"] and must NOT consume the next note ID. The next
successful add_note on the same ticket uses the same number that
would have been used by the failed call.

No partial mutation: on any failure, tickets, ticket, and
ticket["notes"] are unchanged. Return the error and stop.

12.4 get_ticket_notes — shape and rationale
get_ticket_notes(tickets, ticket_id) -> (True, list[dict]) | (False, message)

Ticket not found → (False, "No ticket with ID {ticket_id}.")

Ticket found, zero notes → (True, [])

Ticket found, notes present → (True, [<note>, ...]) in note-ID order.

Rationale for the (ok, payload) shape (deliberate, not accidental):

work_queue and build_report return bare lists/dicts because they take
no user-typed input and cannot fail. get_ticket_notes takes a
user-typed ID, so a mistyped ID is a real user error. A bare-list return
would make "ticket doesn't exist" indistinguishable from "ticket exists
but has no notes" — both would return [], and the CLI could not tell
the user which case applied.

This is a deliberate use of §3's (ok, payload) convention, not an
exception to it.

12.5 next_note_id(ticket)
Pure helper. Returns f"N{n:03d}" where n is
max(int(existing_note["note_id"][1:]) for existing_note in ticket["notes"]) + 1,
or 1 if ticket["notes"] is empty.

Uses max+1 — not len+1 — for the same reason ticket IDs do
(see create_ticket). A note deleted from the list must not cause
the next note to reuse an old ID.

12.6 Status rules
Only tickets with status in {"open", "in_progress"} accept new notes.
A resolved ticket rejects note addition with a message that points at
reopen_ticket. After reopening, the ticket's status is open again,
and notes are accepted — no special-case code, the check falls out of
the current status.

Notes are preserved through resolve and reopen. Reopening does
not clear ticket["notes"].

12.7 Storage obligations
save_tickets writes the extended ticket dict (including notes).

load_tickets must validate notes for every ticket on load:

notes key present, value is a list.

Every note is a dict with keys note_id, author, message.

note_id matches ^N\d+$.

note_id unique within a ticket (by int(note_id[1:]), mirroring the
ticket-ID rule in §2).

author non-empty after .strip().

message length 5–300 after .strip().

Any violation raises CorruptDataError and the entire load fails —
current in-memory state is not replaced. This is the same
validate-before-replace rule as §2.

12.8 Tests
Required test cases for notes:

Add note to an open ticket — success, note ID is N001.

Add a second note to the same ticket — note ID is N002.

Add a note to a ticket with a gap in note IDs — next ID is max+1.

Reject a note on a resolved ticket — no state change.

After reopen, a note can be added — status is open.

Reject a blank author — no state change, no ID consumed.

Reject a message shorter than 5 chars — no state change.

Reject a message longer than 300 chars — no state change.

Reject a note for an unknown ticket ID — no state change.

Failed attempt does not consume the next note ID: fail one attempt,
then succeed; the successful note should carry the ID that the failed
attempt would have used.

get_ticket_notes on a valid ticket with no notes returns (True, []).

get_ticket_notes on a nonexistent ticket returns (False, msg).

Save + reload preserves notes and next note ID.

load_tickets rejects a ticket whose note has a bad shape
(missing key, bad note_id, blank author, wrong-length message).

12.9 Reopened-ticket counting (open coordination item)
The report enhancement needs a metric for "reopened tickets". The
current schema does not record whether a ticket has been reopened.
Two options under discussion:

Option 1: Add a boolean was_reopened field to the ticket, set to
True by reopen_ticket. Costs one field; survives save/load.

Option 2: Do not count "reopened" separately — fold into
"currently open" (a reopened ticket is simply open).

Decision deferred to a separate mini-discussion before report
implementation. Whichever is chosen must be recorded in this section
before report code is written.

text

---

## Step 3 — Save and verify

Press `Ctrl+S`.

Then in the terminal:

```bash
wc -l docs/design-decisions.md
grep -c "^## " docs/design-decisions.md
tail -5 docs/design-decisions.md
