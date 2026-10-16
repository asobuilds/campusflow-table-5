# Individual Reflections — CampusFlow Next

## Engineer A — Agene Okoh

**One verified mistake I made.**
When I extended `load_tickets` to require the `notes` field per §12.1, 14
existing storage tests failed. My first instinct was to make `notes` optional.
Checking the design doc showed `notes` is required on every ticket, and the
real fix was in the shared test fixture helper `raw_ticket()` — one function,
two lines. Lesson: when a required schema field is added, the failure surfaces
wherever fixtures are built, not in the production code. The design doc
decides which side is right.

**One learning gain.**
The difference between a schema field that must raise on absence (`notes`) and
one that must tolerate absence for legacy compatibility (`was_reopened`). The
test: *could a correctly behaving older version of the software have written
this file without that key?* If yes → documented default (§12.9). If no →
raise. That distinction is not obvious and I would not have seen it without
the design-doc conversation with B.

**One improvement received through code review.**
In the previous sprint, B's review of my PR found a real bug: `int(None)`
raises `TypeError`, not `ValueError`, so my `except ValueError` let it escape.
B's review was specific — quoted the line, reproduced the bug, cited the
design contract. That set the standard I tried to match when reviewing B's
work in this sprint.

## Engineer B — Emmanuel Elaigwu

One verified mistake I made. During the integration of ticket search, filtering, and notes into the CampusFlow CLI, I encountered Git merge conflicts involving the feature handlers, menu options, and menu dispatch logic. The competing changes assigned different functions to the same menu options. I learned that resolving a merge conflict requires more than removing Git's conflict markers: I must understand the purpose of each change, preserve all required features, and ensure that the menu options call the correct handlers. The lesson is to inspect the surrounding code and verify the integration rather than accepting one branch's changes blindly.
One learning gain. I improved my understanding of how application features depend on one another. For example, adding a note requires more than implementing add_note(); the CLI must collect the required input, call the service, handle errors, persist the updated data, and provide feedback to the user. Similarly, the menu display and dispatch logic must use consistent option numbers. This helped me understand that a feature is not complete simply because its core function exists; it must also integrate correctly with the rest of the application.
One improvement received through code review. During the integration work, I learned the importance of checking the actual menu and existing function names before applying suggested changes. Reviewing the complete menu revealed that option 7 was already assigned to Summary Report, so assigning Search Tickets to option 7 would have introduced another inconsistency. Keeping the established menu structure and mapping Search, Add Note, View Notes, and Filter to options 8, 9, 10, and 11 respectively helped clarify how the features should work together. This reinforced the importance of reviewing changes against the existing implementation rather than making assumptions.