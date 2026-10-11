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
