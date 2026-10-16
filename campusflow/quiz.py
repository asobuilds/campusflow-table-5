"""Question bank for the Engineering Understanding Check."""

QUESTIONS = [
    {
        "question": (
            "Ticket T001 is open and unassigned. "
            "A user tries to move it to in_progress. What should happen?"
        ),
        "options": {
            "A": "Accept the transition",
            "B": "Reject and preserve all data",
            "C": "Resolve it automatically",
            "D": "Remove the ticket",
        },
        "answer": "B",
    },
    {
        "question": (
            "The app has zero tickets. "
            "What should the resolution percentage display?"
        ),
        "options": {
            "A": "Crash",
            "B": "100%",
            "C": "0%",
            "D": "Divide by one without explanation",
        },
        "answer": "C",
    },
    {
        "question": (
            "A user filters by title='wifi', category='Network', "
            "and status='open'. Which records should match?"
        ),
        "options": {
            "A": "Any record matching one filter",
            "B": "Only records matching all supplied filters",
            "C": "All network records",
            "D": "All open records",
        },
        "answer": "B",
    },
    {
        "question": "A resolved ticket receives an Add Note request. What should happen?",
        "options": {
            "A": "Append the note anyway",
            "B": "Delete old notes",
            "C": "Reject until the ticket is reopened",
            "D": "Change the status silently",
        },
        "answer": "C",
    },
    {
        "question": (
            "The JSON file contains two tickets with the same ID. "
            "What should loading do?"
        ),
        "options": {
            "A": "Keep both tickets",
            "B": "Replace memory with duplicates",
            "C": "Reject the load without changing current memory",
            "D": "Rename IDs silently",
        },
        "answer": "C",
    },
    {
        "question": (
            "A pull request changes validation but has no negative-case tests. "
            "What is the best review action?"
        ),
        "options": {
            "A": "Approve because the code runs",
            "B": "Request focused tests and reasoning",
            "C": "Merge immediately",
            "D": "Ask AI to approve it",
        },
        "answer": "B",
    },
]