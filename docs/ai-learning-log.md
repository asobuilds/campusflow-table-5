# AI Learning Log — CampusFlow

Per the Fellows' Guide §5.3. One entry per meaningful AI interaction.

**Minimum: THREE entries per fellow. At least ONE must document an AI suggestion
that was corrected, improved, or rejected after independent verification.**

> **Honesty rule:** do not fabricate a flaw, and do not claim to have verified
> something you did not actually run.

---

## Fellow: Eyung Emmanuel (Engineer B)

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

- **Related file/commit:** `campusflow/reports.py` (`work_queue`), `tests/test_reports.py` — test asserting `T999` sorts before `T1000`. Issue #4. _Commit SHA to be filled in after the F5 commit._

- **What I can now explain without AI:** "T005 comes out first since it first arrived" — the tie is decided by arrival order, not by the ticket ID, so the bare key gives a different queue depending on the order the file happened to be in.

### Interaction #2 — JSON round-trip, and the cost of catching exceptions too broadly

_Feature: F7 (persistence)_

- **Problem:** <what I needed to learn>
- **My initial understanding:** <in my own words — written BEFORE consulting AI>
- **Prompt to AI:** <my actual prompt>
- **Useful AI guidance:** <brief summary of what came back>
- **My independent experiment/test:** <the snippet I ran; what I predicted vs. observed>
- **Verification source or result:** <actual output, test result, or reference URL>
- **Decision:** <accepted / improved / rejected — and why>
- **Related file/commit:** <path, test name, SHA, or PR link>
- **What I can now explain without AI:** <my words>

### Interaction #3 — <topic chosen during Phase 4>

_Reserved. The guide requires one further entry completed while coding/debugging._

---

## Fellow: Agene Okoh (Engineer A)

_To be completed by Engineer A. Own your own entries — do not let your partner write them._
