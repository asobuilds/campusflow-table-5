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
    plus `notes` (a list of validated note dicts) and `was_reopened` (a bool).
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
        "notes",
    )
    normalized = []

    for ticket in data:
        # 5a. Each element must be an object.
        if not isinstance(ticket, dict):
            raise CorruptDataError("Each ticket must be a JSON object")

        # 5b. All nine required keys must be present.
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

        # 5h. was_reopened: legacy tickets may not have it.
        #     §12.9: missing key -> default False (documented exception to §2).
        #     Present but not a bool -> CorruptDataError (corruption, not legacy).
        raw_was_reopened = ticket.get("was_reopened", False)
        if not isinstance(raw_was_reopened, bool):
            raise CorruptDataError(
                f"Invalid was_reopened: {raw_was_reopened!r}")

        # 5i. notes: must be a list. Each note validated (§12.7):
        #     - dict with keys note_id, author, message
        #     - note_id matches ^N\d+$ and is unique within this ticket
        #       (compared by numeric value: N7 and N007 collide, like T7/T007)
        #     - author non-empty after .strip()
        #     - message length 5..300 after .strip()
        raw_notes = ticket["notes"]
        if not isinstance(raw_notes, list):
            raise CorruptDataError("notes must be a list")

        notes = []
        seen_note_ids = set()
        for note in raw_notes:
            if not isinstance(note, dict):
                raise CorruptDataError("Each note must be a JSON object")
            for nkey in ("note_id", "author", "message"):
                if nkey not in note:
                    raise CorruptDataError(
                        f"Note missing required key: {nkey}")

            raw_note_id = note["note_id"]
            if (not isinstance(raw_note_id, str)
                    or not re.match(r"^N\d+$", raw_note_id)):
                raise CorruptDataError(
                    f"Invalid note_id: {raw_note_id!r}")
            note_num = int(raw_note_id[1:])
            if note_num in seen_note_ids:
                raise CorruptDataError(
                    f"Duplicate note_id by numeric value: {raw_note_id!r}")
            seen_note_ids.add(note_num)
            note_id = f"N{note_num:03d}"

            raw_author = note["author"]
            if not isinstance(raw_author, str) or not raw_author.strip():
                raise CorruptDataError(
                    f"Invalid note author: {raw_author!r}")

            raw_message = note["message"]
            if not isinstance(raw_message, str):
                raise CorruptDataError(
                    f"Invalid note message: {raw_message!r}")
            message = raw_message.strip()
            if len(message) < 5:
                raise CorruptDataError(
                    "Note message must be at least 5 characters")
            if len(message) > 300:
                raise CorruptDataError(
                    "Note message must be at most 300 characters")

            notes.append({
                "note_id": note_id,
                "author": raw_author.strip(),
                "message": message,
            })

        # 5j. Build a NEW dict — never mutate the parsed input.
        normalized.append({
            "id": ticket_id,
            "title": title,
            "category": category,
            "urgency": urgency,
            "affected_users": affected_users,
            "priority": priority,
            "status": status,
            "assigned_to": assigned_to,
            "notes": notes,
            "was_reopened": raw_was_reopened,
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
