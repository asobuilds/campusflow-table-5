# AI Learning Log — CampusFlow

Two fellows, one file. Rule: each fellow edits ONLY he's own section and
appends to the END of that section. If we collide at merge time, follow §4.6
of the Fellows' Guide: inspect the conflict markers, keep both, resolve on the
branch, rerun tests.

---

## Fellow: Agene (Engineer A)

### Interaction #1 — <concept/topic>

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

## Fellow: Eyung (Engineer B)

### Interaction #1 — <concept/topic>

(same template)