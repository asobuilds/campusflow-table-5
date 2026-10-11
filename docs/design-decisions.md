# CampusFlow — Design Decisions

Agreed by Engineer A (Agene) and Engineer B (Eyung) before any code is written.
Frozen after the first review round.

## 1. Error handling

- **User errors** (things a person can fix by typing differently): functions return a tuple `(ok, payload)`.
  - `ok = True`  → `payload` is the successful data (e.g., a ticket dictionary).
  - `ok = False` → `payload` is a short message the CLI will print.
- **Structural errors** (broken data files, missing keys): we raise `CorruptDataError`.
  - Defined in `campusflow/errors.py`.
  - This file imports nothing from the rest of the project (it is a "leaf" module).
  - Raised from `storage.py` and `workflow.py` when the data itself is broken.

## 2. Normalization contract (CRITICAL — do not skip)

- `validate_ticket_input(title, category, urgency, affected_users)` is a PURE function.
  - No list access. No mutation. No side effects. Just data in, data out.
  - Returns `(True, (title, category, urgency, affected_users))` with values normalized, OR `(False, "error message")`.
- Normalization rules:
  - `title` is stripped of leading/trailing spaces.
  - `category` is matched case-insensitively and stored as `Network` / `Hardware` / `Software` / `Other`.
  - `urgency` is lowercased to `low` / `medium` / `high`.
  - `affected_users` is parsed from the raw value (which may be a string from `input()`).
- A blank title (after `.strip()`) → `(False, "Title cannot be blank")`.
- Booleans are rejected FIRST in the affected_users validator: `isinstance(x, bool)` returns `(False, "affected_users must be a positive whole number")`. Reason: `True == 1` in Python; a hand-edited JSON with `"affected_users": true` must not become 1.
- `calculate_priority(urgency, affected_users)` REQUIRES ALREADY-NORMALIZED input.
  - It compares `urgency == "high"` literally, using lowercase.
- Every entry point that stores urgency MUST normalize first:
  - `create_ticket` — calls `validate_ticket_input`.
  - `storage.load_tickets` — re-normalizes each ticket after reading JSON (defensive against hand-edited files).
- `load_tickets` normalization rules:
  - Case variation of `low` / `medium` / `high` → normalize.
  - Unknown value (e.g., `"urgent"`) OR missing key → raise `CorruptDataError`.
  - Never pass through an unnormalized value; never default it.
- Test obligation: `urgency="High", affected_users=2` must return priority `"high"`, not `"low"`.

## 3. Return shape

- Every public function returns `(ok, payload)`.
- Slot 2 is only meaningful after checking that slot 1 is True.

### Deliberate exceptions to `(ok, payload)`

Two different kinds of exception. Do not conflate them.

- **Pure projections** — `work_queue(tickets)` returns `list[dict]` and `build_report(tickets)` returns `dict`, directly.
  - Reason: pure projections over in-memory data. Nothing user-fixable can fail. A flag nobody checks is ceremony.
- **Load-or-raise** — `load_tickets(path)` returns `list[dict]` OR raises `CorruptDataError`.
  - Reason: this is §1's contract, not a special case. Structural failure is an exception, not a user error.
- `save_tickets(tickets, path)` returns `None`.

## 4. Mutation model

- `create_ticket(tickets, ...)` appends the new ticket dict to `tickets` AND returns `(True, new_dict)`.
- `assign_ticket(tickets, ticket_id, name)` mutates the dict in place and returns `(True, same_dict)`.
- No copies are made. `json.dump(tickets, ...)` writes the live list directly.

## 5. Function signatures (frozen)

```python
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