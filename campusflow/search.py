def search_tickets(tickets, query):
    """Return tickets matching a case-insensitive partial-text search."""

    # An empty query should not match every ticket.
    if not isinstance(query, str) or not query.strip():
        return []

    query = query.strip().casefold()

    searchable_fields = (
        "id",
        "title",
        "category",
        "urgency",
        "priority",
        "status",
        "assigned_to",
    )

    # Build a new list without changing the original tickets.
    return [
        ticket
        for ticket in tickets
        if any(
            query in str(ticket.get(field) or "").casefold()
            for field in searchable_fields
        )
    ]

def filter_tickets(tickets, status=None, priority=None, category=None):
    """Return tickets matching all supplied filters."""

    filters = {
        "status": status,
        "priority": priority,
        "category": category,
    }

    # Reject invalid filter types instead of crashing.
    if any(
        value is not None and not isinstance(value, str)
        for value in filters.values()
    ):
        return []

    # Normalize supplied filters for case-insensitive matching.
    filters = {
        field: value.strip().casefold()
        for field, value in filters.items()
        if value is not None
    }

    return [
        ticket
        for ticket in tickets
        if all(
            str(ticket.get(field) or "").casefold() == value
            for field, value in filters.items()
        )
    ]