"""Shared exception types for CampusFlow.

This module imports nothing from the rest of the project. It is a "leaf"
module, so any other module can import from it without creating a
circular dependency.
"""


class CorruptDataError(Exception):
    """Raised when persisted data is structurally broken.

    Examples:
      - A ticket dictionary is missing a required key.
      - A JSON file is malformed.
      - A field has an illegal value that cannot be normalized
        (e.g., urgency == "urgent").
    """
    pass