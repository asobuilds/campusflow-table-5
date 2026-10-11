def validate_ticket_input(title, category, urgency, affected_users):
    """
    Pure function. Data in, data out. No side effects, no mutation,
    no I/O, no printing.

    Returns:
        (True, (title, category, urgency, affected_users)) if all four
            inputs are valid after normalization.
        (False, "human-readable message") on the first failure.

    Check order matters — return the FIRST failure, don't check the rest:
        1. title
        2. category
        3. urgency
        4. affected_users
    """
    # 1. TITLE
    if not isinstance(title, str):
        return (False, "Title must be text")
    title = title.strip()
    if not title:
        return (False, "Title cannot be blank")

    # 2. CATEGORY
    if not isinstance(category, str):
        return (False, "Category must be one of: Network, Hardware, Software, Other")
    category = category.lower()
    categories = {
        "network": "Network",
        "hardware": "Hardware",
        "software": "Software",
        "other": "Other",
    }
    if category not in categories:
        return (False, "Category must be one of: Network, Hardware, Software, Other")
    category = categories[category]

    # 3. URGENCY
    if not isinstance(urgency, str):
        return (False, "Urgency must be one of: low, medium, high")
    urgency = urgency.lower()
    if urgency not in {"low", "medium", "high"}:
        return (False, "Urgency must be one of: low, medium, high")

    # 4. AFFECTED_USERS
    # bool must be rejected BEFORE int: True == 1 in Python.
    if isinstance(affected_users, bool):
        return (False, "affected_users must be a positive whole number")
    if isinstance(affected_users, float):
        return (False, "affected_users must be a positive whole number")
    if isinstance(affected_users, int):
        count = affected_users
    else:
        try:
            count = int(affected_users)
        except ValueError:
            return (False, "affected_users must be a positive whole number")
    if count <= 0:
        return (False, "affected_users must be a positive whole number")

    return (True, (title, category, urgency, count))


def calculate_priority(urgency, affected_users):
    """
    Returns one of: "critical", "high", "medium", "low".

    ASSUMES urgency has already been normalized to lowercase
    ("low", "medium", "high") and affected_users is a positive int.
    Does NOT validate or normalize — the caller (create_ticket or
    load_tickets) is responsible for that.
    """
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


def create_ticket(tickets, title, category, urgency, affected_users):
    """
    Validates input, generates the next unique ticket ID, computes
    priority, builds the ticket dict, appends it to `tickets`, and
    returns (True, ticket_dict).

    On validation failure, returns (False, "message") and does NOT
    append anything to `tickets`.

    `tickets` is a list of dicts. Each dict is assumed to have an
    "id" key (load_tickets is responsible for enforcing structure;
    this function trusts the in-memory list).
    """
    result = validate_ticket_input(title, category, urgency, affected_users)
    if result[0] is False:
        return (False, result[1])

    _, (title, category, urgency, affected_users) = result

    # Next ID: take the highest existing number and add one. Using max+1
    # (not len+1) makes this gap-safe: [T001, T003] -> T004, and it can
    # never collide with an existing id after deletions.
    if not tickets:
        new_id = "T001"
    else:
        highest = max(int(t["id"][1:]) for t in tickets)
        new_id = f"T{highest + 1:03d}"

    priority = calculate_priority(urgency, affected_users)

    ticket = {
        "id": new_id,
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": priority,
        "status": "open",
        "assigned_to": None,
    }

    tickets.append(ticket)
    return (True, ticket)
