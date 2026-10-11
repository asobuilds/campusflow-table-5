import json
import os
import re

from campusflow.errors import CorruptDataError
from campusflow.tickets import validate_ticket_input


def load_tickets(path):
    """
    Load and normalize tickets from the JSON file at `path`.

    Returns a list of ticket dicts. Returns [] when the file is absent
    or whitespace-only (the "no data yet" cases). Raises CorruptDataError
    on any structural problem: bad JSON, a non-list top level, a non-dict
    ticket, a missing required key, an unnormalizable field, or duplicate
    ticket ids.

    Every returned dict is newly built with these keys in order:
        id, title, category, urgency, affected_users,
        priority, status, assigned_to
    """
    # 1. Absent file is not an error — nothing has been saved yet.
    if not os.path.exists(path):
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    # 2. An empty (or whitespace-only) file is treated the same as absent.
    if not raw.strip():
        return []

    # 3. Bad JSON is a structural failure.
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise CorruptDataError(f"Malformed JSON in {path}: {exc}")

    # 4. The top level must be a list of tickets.
    if not isinstance(data, list):
        raise CorruptDataError("Top-level JSON must be a list of tickets")

    required_keys = (
        "id", "title", "category", "urgency",
        "affected_users", "priority", "status", "assigned_to",
    )
    normalized = []

    for ticket in data:
        # 5a. Each element must be an object.
        if not isinstance(ticket, dict):
            raise CorruptDataError("Each ticket must be a JSON object")

        # 5b. All eight keys must be present.
        for key in required_keys:
            if key not in ticket:
                raise CorruptDataError(f"Ticket missing required key: {key}")

        # 5c. id: "T" followed by digits; re-pad to 3 digits ("T7" -> "T007").
        raw_id = ticket["id"]
        if not isinstance(raw_id, str) or not re.match(r"^T\d+$", raw_id):
            raise CorruptDataError(f"Invalid ticket id: {raw_id!r}")
        ticket_id = f"T{int(raw_id[1:]):03d}"

        # 5d. Reuse the shared validator for the four input fields.
        #     Its (False, msg) is a structural problem here, so raise.
        ok, payload = validate_ticket_input(
            ticket["title"],
            ticket["category"],
            ticket["urgency"],
            ticket["affected_users"],
        )
        if not ok:
            raise CorruptDataError(payload)
        title, category, urgency, affected_users = payload

        # 5e. priority: stored as-is (lowercased), never recomputed.
        raw_priority = ticket["priority"]
        if not isinstance(raw_priority, str):
            raise CorruptDataError(f"Invalid priority: {raw_priority!r}")
        priority = raw_priority.strip().lower()
        if priority not in {"critical", "high", "medium", "low"}:
            raise CorruptDataError(f"Invalid priority: {raw_priority!r}")

        # 5f. status: stored as-is (lowercased).
        raw_status = ticket["status"]
        if not isinstance(raw_status, str):
            raise CorruptDataError(f"Invalid status: {raw_status!r}")
        status = raw_status.strip().lower()
        if status not in {"open", "in_progress", "resolved"}:
            raise CorruptDataError(f"Invalid status: {raw_status!r}")

        # 5g. assigned_to: None, or a non-empty string after stripping.
        raw_assigned = ticket["assigned_to"]
        if raw_assigned is None:
            assigned_to = None
        elif isinstance(raw_assigned, str) and raw_assigned.strip():
            assigned_to = raw_assigned.strip()
        else:
            raise CorruptDataError(f"Invalid assigned_to: {raw_assigned!r}")

        # 5h. Build a NEW dict — never mutate the parsed input.
        normalized.append({
            "id": ticket_id,
            "title": title,
            "category": category,
            "urgency": urgency,
            "affected_users": affected_users,
            "priority": priority,
            "status": status,
            "assigned_to": assigned_to,
        })

    # 6. Duplicate ids compared by numeric value (T7 and T007 collide).
    seen = set()
    for t in normalized:
        n = int(t["id"][1:])
        if n in seen:
            raise CorruptDataError(
                f"Duplicate ticket id by numeric value: {t['id']}")
        seen.add(n)

    # 7.
    return normalized


def save_tickets(tickets, path):
    """
    Write `tickets` (a list of dicts) to JSON at `path`, creating the
    parent directory if needed. Returns None.

    No try/except: a write failure (disk full, permissions) propagates to
    the caller, which decides how to surface it — this is not a
    user-fixable error.
    """
    parent = os.path.dirname(path)
    if parent:  # Empty dirname means the current directory; nothing to make.
        os.makedirs(parent, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(tickets, f, indent=2)

    return None
