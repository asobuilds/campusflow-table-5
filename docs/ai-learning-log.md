# AI Learning Log — CampusFlow

Two fellows, one file. Rule: each fellow edits ONLY their own section and
appends to the END of that section. If we collide at merge time, follow §4.6
of the Fellows' Guide: inspect the conflict markers, keep both, resolve on the
branch, rerun tests.

Guide requirement: THREE entries per fellow. At least ONE must document an AI
suggestion that was corrected, improved or rejected after independent
verification. Do not fabricate a flaw, and do not claim to have verified
something you did not run.

---

## Fellow: Agene (Engineer A)

### Interaction #1 — Python bools vs ints in type checking

Problem:My `validate_ticket_input` needs to reject `affected_users=True`, but Python treats True as an integer (`isinstance(True, int) is True`). `isinstance(x, int)` would let booleans through.

My initial understanding: isinstance(x, int) would suffice because True is not really a number

Prompt to AI: "In Python, if I check isinstance(affected_users, int) and someone passes True, does it pass or fail? Show me a five-line example unrelated to my project."

Useful AI guidance: AI showed that `True == 1` is `True`, and `isinstance(True, int)` returns `True`. Suggested checking `isinstance(x, bool)` **before** isinstance(x, int)

My independent experiment/test: Ran `python3 -c "print(isinstance(True, int), isinstance(True, bool), True == 1)"` — confirmed all three print `True True True`.

Verification source or result: Python docs on `bool` — "Booleans are a subtype of integers." Also confirmed by the test `test_affected_users_bool_rejected`, which asserts `create_ticket(..., True)` returns `(False, msg)`.

Related file/commit: `campusflow/tickets.py` line ~60; commit `d62701a`; test `test_affected_users_bool_rejected`.

What I can now explain without AI: In Python, `bool` is a subclass of `int`. Any type-check that distinguishes them must check `bool` first, or `True` silently becomes `1`.

### Interaction #2 — Exception hierarchy: TypeError vs ValueError

Problem: B (partner review) found that `int(None)` raises `TypeError`, not `ValueError`. My `except ValueError` missed it — so `validate_ticket_input(None, ...)` crashed the whole program instead of returning `(False, msg)`.

My initial understanding: `int()` always raises `ValueError` on bad input.

Prompt to AI: "What exception does int(None) raise in Python 3? What about int([])? Compare to int('abc'). Do not write my project code."

Useful AI guidance: AI explained that `int()` raises `TypeError` when the argument is a non-string non-number (None, list, dict), and `ValueError` when it's a string it can't parse (`"abc"`, `"1.5"`). Suggested `except (TypeError, ValueError)`.

My independent experiment/test: Ran `python3 -c "int(None)"` → `TypeError`. Ran `python3 -c "int('abc')"` → `ValueError`. Confirmed the two are different exception classes.

Verification source or result: Python docs on `int()`: "If x is not a number or if base is given, then x must be a string... Raises ValueError if the string cannot be parsed. Raises TypeError if x is not a string or number." Also confirmed by B's reproduction in PR #9 review, and by new test `test_affected_users_none_rejected`.

Decision: **Accepted, and improved.** Changed `except ValueError` to `except (TypeError, ValueError)`. Added a second test (`test_affected_users_list_rejected`) for the same class of bug from a different shape.

Related file/commit: `campusflow/tickets.py`; commit `95f79e6`; tests `test_affected_users_none_rejected`, `test_affected_users_list_rejected`.

What I can now explain without AI: `int()` has two failure modes with two different exception classes. Any robust parse-and-coerce must catch both, or the caller's error contract leaks as a crash.

### Interaction #3 — Unpacking a nested tuple return value

Problem: After Claude Code wrote `campusflow/storage.py`, the smoke test failed with `ValueError: too many values to unpack (expected 2)`. The bug was in `load_tickets`: it unpacked `validate_ticket_input`'s return value with the wrong shape assumption.

My initial understanding: `validate_ticket_input` returns `(True, (title, category, urgency, affected_users))` — so `ok, payload = result` gives `payload` as the 4-tuple. But Claude Code had written `_, (title, category, urgency, affected_users) = payload` — expecting `payload` to still have the `True` wrapper, which it does not.

Prompt to AI (Claude Code): "Here is the traceback and the code. Explain the exact return shape mismatch. Do not rewrite the file."

Useful AI guidance: Claude Code explained that `payload` is already the inner 4-tuple because `ok, payload = result` stripped the outer wrapper. The second unpacking assumed the wrong shape.

My independent experiment/test: Wrote a small verification at the Python REPL: `result = (True, ('a', 'b', 'c', 1)); ok, payload = result; print(payload)` → confirmed `payload` is `('a', 'b', 'c', 1)`, not `(True, (...))`. Then re-ran the smoke test after the fix: all 6 checks passed.

Verification source or result: Traceback from the smoke test; then successful re-run after the fix; then added `test_validate_returns_two_tuple_with_nested_four_tuple` to pin the exact shape.

Decision: **Corrected.** Claude Code's code was wrong (the nested-tuple assumption was implicit and not spelled out in the task). Fixed manually.

Related file/commit: `campusflow/storage.py`; commit `c0abf12` (fix) and `a6bf0d6` (test to pin shape).

What I can now explain without AI: A return value like `(ok, payload)` where `payload` is itself a tuple is easy to unpack wrong if the caller assumes one level less of nesting. When a function's contract isn't tested for shape, the bug slips to the caller's first run. Pin the shape with an assertion.

---

### Interaction #4 — Test fixture drift when a schema field becomes required

Problem: After extending `load_tickets` to require the new `notes` key
per §12.1, fourteen of the existing storage tests failed with
`CorruptDataError: Ticket missing required key: notes`. The production
code was correct — every test that planted a ticket fixture built it
without `notes`.

My initial understanding: I assumed the failures meant `load_tickets`
had a bug in the new notes handling, or that the `notes` key should be
optional for legacy compatibility.

Prompt to AI: "These 14 storage tests now fail after I made `notes` a
required key. I need to know whether the fix belongs in the loader or
in the tests. Explain how to tell which layer owns the failure, without
rewriting either."

Useful AI guidance: The distinction is ownership of the fixture. The
loader's contract is documented (§12.1: `notes` is required on every
ticket). The tests exist to verify the loader obeys its contract, not
to invent a different one. When a schema field is added, every fixture
that constructs that schema must be updated. Centralized helpers make
this one edit instead of fourteen.

My independent experiment/test: Found that all 14 failing tests built
their fixtures via a single module-level helper, `raw_ticket()`, at
`tests/test_storage.py:49`. Confirmed by `grep -n '"id":' tests/test_storage.py`
that the only other ticket-dict construction was my own `_ticket()`
inside `NotesStorageTests`, which already had the new keys. Fix was two
lines added to `raw_ticket()`.

Verification source or result: Re-ran `python3 -m unittest discover -s
tests -v` after the fix → `Ran 150 tests ... OK`.

Decision: Accepted and applied. Do NOT make `notes` optional in the
loader — that would contradict §12.1 and would leave `add_note` open
to a KeyError on `ticket["notes"]` for any hand-crafted dict.

Related file/commit: `tests/test_storage.py:49` (`raw_ticket` helper);
commit `745cf79`.

What I can now explain without AI: When a required schema field is
added, the failure surfaces wherever fixtures are built, not in the
production code. The design doc decides which side is right; the fix
goes on the side that disagrees with the doc. One centralized fixture
helper means one edit, not N.

### Interaction #5 — Deliberate schema exception: required vs. legacy-compatible keys

Problem: §12.1 makes `notes` required on every ticket. §12.9 makes
`was_reopened` tolerant of absence for legacy files. On the surface
these look contradictory — two new fields with opposite missing-key
rules. I needed to understand why the exception is legitimate rather
than drift.

My initial understanding: A missing key should always raise, per §2
("Unknown value OR missing key → raise CorruptDataError"). The
`was_reopened` exception felt like a special case someone had carved
out.

Prompt to AI: "Explain the difference between a schema field that was
always expected to be there but is missing (corruption) versus a
schema field that is genuinely new (legacy compat). Give a small
example using an unrelated data format."

Useful AI guidance: The question to ask of a missing key is: *could a
correctly behaving older version of the software have produced a file
without this key?* If yes, absence is legacy data and the loader must
tolerate it with a documented default. If no, absence is corruption and
the loader must raise. `notes` was never written by any version that
did not know about notes — its absence is corruption. `was_reopened`
is new; files written before this sprint legitimately lack it. The
difference is not "new vs. old" — it is "could an honest writer have
omitted this?"

My independent experiment/test: Confirmed with a small unrelated test:
a JSON file representing a "product" with a new `currency` field
defaulting to `"USD"` when absent, versus a missing `price` field which
raises. Also confirmed in this project by adding
`test_legacy_ticket_without_was_reopened_loads_as_false` (§12.9
behavior, passes) and `test_notes_field_missing_raises` (§12.1
behavior, passes). The two tests together pin the exception.

Verification source or result: `docs/design-decisions.md` §12.9 —
"Every other missing key still raises. This exception is documented
here so it is not mistaken for drift." Tests:
`test_legacy_ticket_without_was_reopened_loads_as_false`,
`test_notes_field_missing_raises`, `test_non_bool_was_reopened_raises`.

Decision: Accepted as designed. The exception is not drift because the
design doc explicitly names it, explains its scope ("this key only,
missing only"), and pairs it with a negative test on the other side
(the notes case). One-way tolerance without a negative counterpart
would be drift.

Related file/commit: `docs/design-decisions.md` §12.9; commits
`434b2a8` (doc) and `745cf79` (loader).

What I can now explain without AI: The test for whether a missing key
should raise is: "could a correct prior version of the software have
written this file without that key?" If yes → documented default. If
no → raise. The design doc must name every default explicitly, and
each default must be paired with a test on the "should raise" side of
the adjacent field, so the exception cannot silently grow.


## Fellow: Eyung (Engineer B)

### Interaction #1 — Sorting with keys, tie-breaking, and numeric ticket IDs

_Feature: F5 (work queue)_

- **Problem:** F5 requires priority ties to break by "the earlier numeric ticket ID". I did not know how Python's `sorted()` decides order between two items, so I could not tell whether a priority-only sort would satisfy that requirement.

- **My initial understanding:** No idea how `sorted()` decides the order between two items. Recorded plainly, and before any explanation — not dressed up afterwards.

- **Prompt to AI:** "no idea" — said plainly when asked what I understood about how `sorted()` decides order. The AI explained comparison sorting, `key=`, and tuple keys, then had me predict a small example unrelated to CampusFlow before running it.

- **Useful AI guidance:** `sorted()` is a comparison sort — it only ever asks "is this one less than that one?". Plain values already have an ordering (numbers by magnitude, strings lexicographically) but dicts do not, which is why sorting tickets requires `key=`. `key` chooses the ordering and does NOT transform the output. A tuple key compares element by element, left to right, so `(rank, int(id[1:]))` means "order by rank, then break ties by numeric ID". Python's sort is also stable: equal items keep their arrival order.

- **My independent experiment/test:** I predicted two sorts before running them. On `['pear','fig','plum','kiwi','apple']` I predicted the tie between the three 4-letter words would stay in arrival order (`pear, plum, kiwi`) — I ignored the tuple's second element. I then applied it to ticket data, scrambled `T005` before `T001`, both `critical`, and predicted `T005` first "since it first arrived".

- **Verification source or result:** Predicted, then ran it myself:

  ```
  ['T005', 'T001']   # key=lambda x: R[x['priority']]
  ['T001', 'T005']   # key=lambda x: (R[x['priority']], int(x['id'][1:]))
  ```

  Reference: Python docs — Sorting HOW TO, https://docs.python.org/3/howto/sorting.html

- **Decision:** Accepted the explanation. Rejected the stability-dependent sort for F5: the bare-key version returns `T005` first, which is arrival order, not the "earlier numeric ticket ID" the spec requires — it silently fails a stated requirement. F5 uses the tuple key `(rank, int(id[1:]))`.

- **Related file/commit:** `campusflow/reports.py` (`work_queue`), `tests/test_reports.py` — test asserting `T999` sorts before `T1000`. Issue #4. Commit `77a1fef`.

- **What I can now explain without AI:** "T005 comes out first since it first arrived" — the tie is decided by arrival order, not by the ticket ID, so the bare key gives a different queue depending on the order the file happened to be in.

### Interaction #2 — Verifying a claim against the artifact, not the summary

_Feature: F4 (workflow)_

- **Problem:** I needed the exact transition rules before writing `workflow.py`. The AI described them as "the frozen contract, §5/§6/§7 of `docs/design-decisions.md`".

- **My initial understanding:** I assumed that because we had agreed the rules and the document was called frozen, the document contained them. I had never opened it.

- **Prompt to AI:** "fix the §7 reference and start workflow"

- **Useful AI guidance:** Three legal edges — `open → in_progress` (only if assigned), `in_progress → resolved`, `resolved → open` via reopen preserving `assigned_to` — attributed to specific numbered sections of the design document.

- **My independent experiment/test:** Ran `git diff ebc6797 d62701a -- docs/design-decisions.md`. Output was **empty** — the file is identical across both commits. Then read the document itself off A's branch without checking it out: `git show origin/feat/1-ticket-creation:docs/design-decisions.md`.

- **Verification source or result:** The empty diff, plus the fetched file: §1 Error handling, §2 Normalization contract, §3 Return shape, §4 Mutation model, §5 Function signatures — and it stops there, mid-§5. **No transition section, and no §7.** *Update:* A later reported he had "fixed truncation, complete at §1–§11". Re-ran the same command against `af2765d` and it now returns §1–§11: §5 does contain the transition rules (`Status transitions (STRICT)`), §6 covers assignment on a resolved ticket, and §7 exists — it is "Queue ordering", not the exceptions section. So the AI's §7 citation was wrong either way, but "§7 does not exist" was true only of the truncated copy.

- **Decision:** **Rejected** the AI's characterisation on the evidence available: what had been pushed to the branch did not contain the rules, so they existed nowhere either of us could point at. Corrected the §7 citations to §3 — which the restored document confirms is where the exceptions live — and wrote the transition rules into `tests/test_workflow.py` as executable assertions rather than waiting on the document. When the restored §5/§6 appeared they were checked against those assertions, and they agree.

- **Related file/commit:** `docs/design-decisions.md` (§3, §5, §6), `tests/test_workflow.py`, `campusflow/workflow.py`, commit `6a7388d`.

- **What I can now explain without AI:** A design document is only a contract if the rules are actually inside it, and "it's on the branch" is not the same as "it's in my teammate's head". My first check was true but incomplete: I read a truncated file and concluded the rules had never been written down. The lesson is that a claim about a file has a timestamp — when the other person says they changed it, re-read it before repeating what you found.

### Interaction #3 — Checking that a test catches what it claims to catch

_Feature: F5 (work queue)_

- **Problem:** My tie-break test had two assertions and a docstring explaining that each caught a different bug. I needed to know whether that explanation was true before defending it in review.

- **My initial understanding:** The AI wrote the docstring. I had read it and taken it at face value, without testing the claim.

- **Prompt to AI:** The claim was in an AI-written docstring: that the reversed-arrival-order assertion catches "an implementation that pre-sorts the input by ID". I asked the AI to justify it.

- **Useful AI guidance:** The AI asserted that pre-sorting the input by ID, or otherwise relying on sort stability, is what the second assertion catches.

- **My independent experiment/test:** Predicted the outcome first, then built the implementation the docstring said would fail — pre-sort by numeric ID, then a stable sort by priority only:

  ```python
  RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

  def variant(tickets):
      ordered = sorted(tickets, key=lambda t: int(t["id"][1:]))    # pre-sort by ID
      return sorted(ordered, key=lambda t: RANK[t["priority"]])     # then by priority
  ```

  Ran it over the tie-break pair in both arrival orders.

- **Verification source or result:** Both arrival orders printed `['T999', 'T1000']`. The variant is correct, so it passes both assertions.

- **Decision:** **Rejected** the docstring's claim. Pre-sorting by ID is not a bug — it produces exactly the same order as the tuple key, just less directly. The reversed-order assertion actually catches a key with **no** tie-break at all (priority only), which returns `T1000` first when the input arrives reversed. Corrected the docstring to say that.

- **Related file/commit:** `tests/test_reports.py`, `test_tie_break_is_numeric_not_lexicographic`, commit `77a1fef`.

- **What I can now explain without AI:** A comment in a test is a claim like any other. Two assertions can look like belt-and-braces while actually testing the same thing; the only way to know which bug each one catches is to build the broken version and watch which line fails.

### Interaction #4 — Cross-module invariant: string validation vs. numeric tie-breaking

_Feature: F7 (persistence) and F5 (work queue)_

- **Problem:** When specifying `load_tickets` in `storage.py`, Engineer A proposed validating ticket IDs with regex `^T\d+$` and checking uniqueness as raw strings across the file. I needed to verify whether string-based uniqueness and unpadded IDs would preserve the queue ordering contract in `reports.py`.

- **My initial understanding:** The AI drafted `tests/test_storage.py` and left the handling of ID format and padding marked `OPEN`. I initially assumed A's string-level `^T\d+$` check would be sufficient since `create_ticket` produces well-formed strings.

- **Prompt to AI:** "If load_tickets accepts any ^T\d+$ string and checks uniqueness on raw strings, what happens in work_queue if a hand-edited file contains both 'T7' and 'T007'?"

- **Useful AI guidance:** The AI pointed out that `work_queue` sorts on `(RANK[priority], int(id[1:]))`. As integers, `int("7") == int("007") == 7`. If distinct string IDs with the same numeric value exist in the store, the numeric tie-break produces an exact tie and falls back to arrival order — reintroducing the exact non-deterministic queue ordering that §7 exists to eliminate.

- **My independent experiment/test:** Applied Engineer A's own stated design principle: *"load_tickets is a normalizer, not a validator; accept anything that can be normalized to what create_ticket writes."* Since `create_ticket` formats IDs as `f"T{n:03d}"`, `"T7"` should normalize to `"T007"`. Furthermore, uniqueness in `load_tickets` cannot be checked on strings; it must be checked on `int(id[1:])` so that `"T7"` and `"T007"` collide and raise `CorruptDataError`. I wrote two test cases to verify this distinction: `test_id_is_zero_padded_to_three_digits` and `test_duplicate_ids_by_numeric_value_raise`.

- **Verification source or result:** Proposed this analysis to Engineer A during PR review. Engineer A accepted the rationale and updated the §2 decision table in `docs/design-decisions.md`: `"T7"` normalizes to `f"T{int(id[1:]):03d}"`, and uniqueness across the loaded file is enforced on `int(id[1:])`. Verified with all 40 tests passing in `tests/test_storage.py`.

- **Decision:** **Accepted and extended** the normalization principle: evaluation of an AI-generated test scaffolding led to identifying where a teammate's spec contradicted an invariant in another module. Enforcing canonical representation at the boundary prevented a subtle sorting bug downstream.

- **Related file/commit:** `docs/design-decisions.md` (§2 decision table), `campusflow/storage.py`, `tests/test_storage.py` (`test_id_is_zero_padded_to_three_digits`, `test_duplicate_ids_by_numeric_value_raise`), commit `1a87df8`.

- **What I can now explain without AI:** Boundary normalization must do more than check local syntax; it must produce the canonical form expected by downstream modules. If two syntactically valid inputs normalize to the same semantic identity, uniqueness must be enforced on that semantic identity, or downstream tie-breaking breaks silently.

