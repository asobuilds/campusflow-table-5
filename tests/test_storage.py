"""Tests for campusflow.storage — F7 PERSISTENCE.

Ownership: design decisions §8 gives storage.py to Engineer A (code) and this
file to Engineer B (tests).

Contract, from docs/design-decisions.md:
  §2  load_tickets obligations — re-normalize every ticket after reading JSON,
      raise CorruptDataError on an unknown value or a missing key, and never
      pass through an unnormalized value or default one.
  §3  load-or-raise: load_tickets returns list[dict] or raises CorruptDataError.
      save_tickets returns None. Neither uses the (ok, payload) tuple.
  §4  no copies — json.dump writes the live list.

Markers, so the source of each expectation is visible:

  [§n]        required by the design document, cited.
  [table]     settled by Engineer A's load_tickets decision table (PR #9 review).
  INFERRED    not written down, but follows from a rule that is. Argue with it.
  ASSUMPTION  my own choice about behaviour the document does not cover.
  OPEN        explicitly unsettled. A pass here is not agreement.

Several expectations began as INFERRED or ASSUMPTION and have since been
confirmed against the decision table, so they now carry [table]. One detail is
still OPEN and says so in place: whether a loaded ticket RETAINS an extra key.

The governing rule, in Engineer A's words: load_tickets is a normalizer, not a
strict type validator. Accept anything that can be normalized to what
create_ticket writes; reject anything that cannot.

THIS FILE CANNOT PASS YET. campusflow/storage.py does not exist, so the import
at the top fails and discovery reports an error for this file. It is left
uncommitted until the module lands.

ALL SIX FIELDS ARE NOW SPECIFIED. status, assigned_to and id were flagged to
Engineer A as unreachable by the first decision table; he specced them, and the
tests below cover all three. Each docstring quotes the rule it encodes, so a
disagreement can be located without re-reading the conversation.
"""

import json
import os
import tempfile
import unittest

from campusflow.errors import CorruptDataError
from campusflow.storage import load_tickets, save_tickets


def raw_ticket(ticket_id="T001", **overrides):
    """A well-formed ticket as it would appear in a hand-written JSON file.

    Built as a plain dict rather than through create_ticket, because these tests
    are about what load_tickets does with a file the app never wrote.
    """
    ticket = {
        "id": ticket_id,
        "title": "Wi-Fi down in Lab 2",
        "category": "Network",
        "urgency": "high",
        "affected_users": 3,
        "priority": "high",
        "status": "open",
        "assigned_to": None,
        "notes": [],
        "was_reopened": False,
    }
    ticket.update(overrides)
    return ticket

class StorageTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = tmp.name
        self.path = os.path.join(self.dir, "tickets.json")

    def write_raw(self, payload):
        """Write payload straight to disk, bypassing save_tickets.

        Hand-editing the store is the exact case §2's load_tickets obligations
        exist for, so the fixture has to be able to produce a file the app would
        never have written itself. A str is written verbatim, so a test can
        plant malformed JSON.
        """
        with open(self.path, "w", encoding="utf-8") as handle:
            if isinstance(payload, str):
                handle.write(payload)
            else:
                json.dump(payload, handle)

    def read_raw(self):
        with open(self.path, encoding="utf-8") as handle:
            return json.load(handle)

    def assertCorrupt(self):
        """Assert load_tickets refuses the planted file.

        Deliberately does not fall back to a partial result: an implementation
        that skips the bad ticket and returns the rest must fail here, because
        that is the "never pass through" rule in §2 being broken quietly.
        """
        with self.assertRaises(CorruptDataError):
            load_tickets(self.path)


class LoadTicketsBasicTests(StorageTestCase):

    def test_missing_file_returns_empty_list(self):
        """[table] A missing file is a fresh start, not broken data.

        Fellows' Guide §1.4 F7: "Missing file should allow a fresh start".
        Contrast with malformed JSON, which raises: missing means "you haven't
        started yet", malformed means "something is broken". That distinction is
        the whole reason the two cases are separate tests.
        """
        self.assertEqual(load_tickets(self.path), [])

    def test_empty_file_returns_empty_list(self):
        """[table] An existing but zero-byte file is also a fresh start.

        Not the same code path as a missing file: this one opens successfully
        and hands json.load an empty string, which raises. The loader has to
        check for it rather than let the parse failure fall through as corrupt.
        """
        self.write_raw("")
        self.assertEqual(load_tickets(self.path), [])

    def test_extra_key_does_not_break_the_load(self):
        """[table] "Ticket has an extra key -> Accept it, ignore the extra".

        The load must succeed. Whether the loaded dict RETAINS the extra key is
        OPEN — I read "accept it" as keeping it, so that load(save(t)) == t
        stays lossless and a field added by a newer version is not silently
        dropped by an older loader. Only the settled half is asserted here.
        """
        extra = raw_ticket()
        extra["reported_by"] = "someone"
        self.write_raw([extra])
        self.assertEqual(load_tickets(self.path)[0]["id"], "T001")

    def test_returns_a_list_of_dicts(self):
        self.write_raw([raw_ticket()])
        result = load_tickets(self.path)
        self.assertIsInstance(result, list)
        self.assertIsInstance(result[0], dict)

    def test_round_trip_is_lossless(self):
        tickets = [
            raw_ticket("T001", status="open"),
            raw_ticket("T002", status="in_progress", assigned_to="Agene"),
            raw_ticket("T003", status="resolved", priority="low"),
        ]
        save_tickets(tickets, self.path)
        self.assertEqual(load_tickets(self.path), tickets)

    def test_empty_store_round_trips(self):
        save_tickets([], self.path)
        self.assertEqual(load_tickets(self.path), [])


class LoadTicketsCorruptDataTests(StorageTestCase):
    """The §2 obligations. Every case here must raise, never recover."""

    def test_malformed_json_raises(self):
        """[§1] a structurally broken file is an exception, not a user error."""
        self.write_raw('{"not": "a list"')
        self.assertCorrupt()

    def test_valid_json_that_is_not_a_list_raises(self):
        """[table] "Top-level JSON is not a list -> Raise CorruptDataError".

        A separate case from the one above, and worth its own test: this file
        parses cleanly, so a loader that only guards the json.load call gets a
        dict back and then iterates it as if it were a list of tickets — walking
        the keys of the wrong object and failing somewhere unrelated to the
        actual problem.
        """
        self.write_raw({"T001": raw_ticket()})
        self.assertCorrupt()

    def test_missing_required_key_raises(self):
        """[§2] "unknown value OR missing key -> raise CorruptDataError"."""
        broken = raw_ticket()
        del broken["urgency"]
        self.write_raw([broken])
        self.assertCorrupt()

    def test_title_must_be_non_blank_text(self):
        """[table] title: non-empty after strip is accepted; "", " " and a
        non-string all raise.

        " " is the case worth having: it passes a naive `if not title` check and
        only fails because the blank test runs after .strip(). A missing "title"
        key is a different rule and is covered by the missing-key test above.
        """
        for bad in ("", " ", None, 42):
            with self.subTest(title=bad):
                self.write_raw([raw_ticket(title=bad)])
                self.assertCorrupt()

    def test_urgency_must_be_a_known_string(self):
        """[table] "urgent" is the document's own example; 42 is the case where
        the value is the right shape of wrong — a number, not a word."""
        for bad in ("urgent", 42):
            with self.subTest(urgency=bad):
                self.write_raw([raw_ticket(urgency=bad)])
                self.assertCorrupt()

    def test_unknown_urgency_is_not_defaulted_to_low(self):
        """[§2] the point of the rule, tested directly.

        An implementation that writes `urgency = urgency or "low"` instead of
        raising passes every other test in this file, because the resulting
        ticket is *shaped* correctly. It is only wrong in what it says. This
        asserts the difference — and separately that priority is not silently
        re-derived from the substituted value.
        """
        self.write_raw([raw_ticket(urgency="urgent", priority="high")])
        with self.assertRaises(CorruptDataError):
            load_tickets(self.path)

    def test_bool_affected_users_raises(self):
        """[§2] a hand-edited "affected_users": true must not become 1.

        §2 puts this rule on validate_ticket_input. load_tickets re-normalizes
        through the same path, so the same guard has to hold here — otherwise
        the store is the way past it.
        """
        self.write_raw([raw_ticket(affected_users=True)])
        self.assertCorrupt()

    def test_affected_users_that_cannot_be_coerced_raises(self):
        """[table] "seven", "", None and [] all raise.

        None and [] are the two that matter beyond storage.py: int(None) and
        int([]) raise TypeError, not ValueError, so they only become
        CorruptDataError if validate_ticket_input catches both. If this test
        reports TypeError instead of a failure, the guard in tickets.py is still
        `except ValueError` and the #9 finding is unfixed — that is exactly what
        this case is here to catch, on the path where it does real damage.
        """
        for bad in ("seven", "", None, []):
            with self.subTest(affected_users=bad):
                self.write_raw([raw_ticket(affected_users=bad)])
                self.assertCorrupt()

    def test_affected_users_create_ticket_would_reject_raises(self):
        """[table] 0, a negative, and a non-whole float all raise on load.

        The rationale is that create_ticket cannot produce any of these, so a
        file containing one is broken rather than a user error. Booleans are the
        fourth member of that set and are covered above, because True == 1 makes
        them the one case where the guard's ORDER matters.
        """
        for bad in (0, -3, 2.5):
            with self.subTest(affected_users=bad):
                self.write_raw([raw_ticket(affected_users=bad)])
                self.assertCorrupt()

    def test_priority_must_be_one_of_the_four(self):
        """[table] "super-high" is a wrong word; 42 is a wrong type."""
        for bad in ("super-high", 42):
            with self.subTest(priority=bad):
                self.write_raw([raw_ticket(priority=bad)])
                self.assertCorrupt()

    def test_category_must_be_a_known_string(self):
        """[table] "Wifi" is close enough to be tempting and still wrong; 42 is
        a wrong type. Originally written here as INFERRED, now confirmed.
        """
        for bad in ("Wifi", "Facilities", 42):
            with self.subTest(category=bad):
                self.write_raw([raw_ticket(category=bad)])
                self.assertCorrupt()

    def test_id_must_be_T_followed_by_digits(self):
        """[table] id must match ^T\\d+$ — uppercase T, one or more digits.

        "t001" is the case that matters most: the same ticket to a human and a
        different one to the program. "T00A" is the one that reaches int() and
        raises ValueError somewhere else entirely if it gets through here.
        """
        for bad in ("t001", "T", "T00A", "001", "", 42):
            with self.subTest(id=bad):
                self.write_raw([raw_ticket(ticket_id=bad)])
                self.assertCorrupt()

    def test_duplicate_ids_raise(self):
        """[table] "Uniqueness enforced across the file — duplicates raise."

        Nothing else in the program can catch this. create_ticket's max+1 cannot
        produce a duplicate, so a file with two tickets sharing an id is only
        reachable by hand-editing — which makes the loader the only place the
        rule can live.
        """
        self.write_raw([raw_ticket("T001"), raw_ticket("T001")])
        self.assertCorrupt()

    def test_duplicate_ids_by_numeric_value_raise(self):
        """[table] Uniqueness is on int(id[1:]), not raw string: T7 and T007 collide."""
        self.write_raw([raw_ticket("T7"), raw_ticket("T007")])
        self.assertCorrupt()


    def test_status_must_be_one_of_three(self):
        """[table] "closed" is the plausible wrong value; 42 is a wrong type.

        This is the field whose failure is quietest: work_queue filters on a
        whitelist, so a status that reaches it unrecognised is dropped from the
        queue with no error at all.
        """
        for bad in ("closed", 42):
            with self.subTest(status=bad):
                self.write_raw([raw_ticket(status=bad)])
                self.assertCorrupt()

    def test_blank_assigned_to_raises(self):
        """[table] None, or a non-empty string after .strip(). "" and " " raise.

        assign_ticket already refuses a blank name, so accepting one on load
        would let the store hold a state the app itself cannot produce — and the
        next save would write it back out as though it were legitimate.
        """
        for bad in ("", " ", 42):
            with self.subTest(assigned_to=bad):
                self.write_raw([raw_ticket(assigned_to=bad)])
                self.assertCorrupt()

    def test_missing_assigned_to_key_raises(self):
        """[table] "Missing key raises; None value is fine." The two halves of
        that sentence are different cases, and only one of them is an error —
        so distinguishing them needs a test that removes the key entirely.
        """
        broken = raw_ticket()
        del broken["assigned_to"]
        self.write_raw([broken])
        self.assertCorrupt()


class LoadTicketsNormalizationTests(StorageTestCase):
    """§2: load_tickets re-normalizes, because the file can be edited by hand."""

    def test_urgency_case_is_normalized(self):
        """[§2] "Case variation of low/medium/high -> normalize"."""
        self.write_raw([raw_ticket(urgency="HIGH")])
        self.assertEqual(load_tickets(self.path)[0]["urgency"], "high")

    def test_category_case_is_normalized(self):
        """[table] "category is 'network' (case variation) -> Normalize to
        'Network', accept". Originally written here as INFERRED.
        """
        self.write_raw([raw_ticket(category="network")])
        self.assertEqual(load_tickets(self.path)[0]["category"], "Network")

    def test_status_case_and_whitespace_are_normalized(self):
        """[table] "OPEN", " In_Progress " -> "open", "in_progress".

        Status is normalized for the same reason urgency is: it is a string the
        program compares against a fixed set, and the comparison is exact.
        Named with the underscore spelling because "in_progress" is the value
        most likely to be retyped wrongly by hand.
        """
        self.write_raw([
            raw_ticket("T001", status="OPEN"),
            raw_ticket("T002", status=" In_Progress "),
        ])
        self.assertEqual(
            [t["status"] for t in load_tickets(self.path)],
            ["open", "in_progress"],
        )

    def test_assigned_to_is_stripped(self):
        """[table] " Agene " -> "Agene".

        Only stripping, not case: a person's name is not a keyword, so there is
        no canonical spelling to normalize it to. This is the one string field
        where the rule is deliberately narrower.
        """
        self.write_raw([raw_ticket(assigned_to=" Agene ")])
        self.assertEqual(load_tickets(self.path)[0]["assigned_to"], "Agene")

    def test_surrounding_whitespace_is_normalized(self):
        """[table] " 7 " -> 7, " Network " -> "Network", " Critical " -> "critical".

        Whitespace is the case a hand-edited file produces most often — a value
        pasted or retyped — and it is the one an exact-match comparison rejects
        while looking like it should work. int() strips its own whitespace, so
        affected_users passes either way; the string fields do not.
        """
        self.write_raw([raw_ticket(
            category=" Network ",
            priority=" Critical ",
            affected_users=" 7 ",
        )])
        loaded = load_tickets(self.path)[0]
        self.assertEqual(loaded["category"], "Network")
        self.assertEqual(loaded["priority"], "critical")
        self.assertEqual(loaded["affected_users"], 7)

    def test_priority_case_is_normalized_without_re_derivation(self):
        """[table] "priority: 'CRITICAL' -> 'critical', accepted."

        This and test_reloaded_priority_is_not_re_derived are two halves of one
        rule and are deliberately separate tests: normalizing the SPELLING of
        the stored value is required, recomputing the VALUE from urgency and
        affected_users is forbidden. An implementation that did the second while
        appearing to do the first passes this test and fails that one.
        """
        self.write_raw([raw_ticket(priority="CRITICAL")])
        self.assertEqual(load_tickets(self.path)[0]["priority"], "critical")

    def test_normalization_applies_to_every_ticket(self):
        """A version that normalizes only the first ticket would pass the two
        tests above. This is the one that catches it."""
        self.write_raw([
            raw_ticket("T001", urgency="HIGH"),
            raw_ticket("T002", urgency="Medium"),
            raw_ticket("T003", urgency="low"),
        ])
        self.assertEqual(
            [t["urgency"] for t in load_tickets(self.path)],
            ["high", "medium", "low"],
        )

    def test_string_affected_users_is_coerced(self):
        """[table] "affected_users: '7' -> 7, accepted."

        This was written as OPEN — §2 argued for coercion from input(), while
        the first decision table's rationale for rejecting 0/-3/2.5/True argued
        for a raise. Engineer A resolved it: load_tickets is a normalizer, not a
        strict type validator. Accept anything that can be normalized to what
        create_ticket writes; reject anything that cannot.
        """
        self.write_raw([raw_ticket(affected_users="7")])
        loaded = load_tickets(self.path)[0]["affected_users"]
        self.assertEqual(loaded, 7)
        self.assertIsInstance(loaded, int)

    def test_id_is_zero_padded_to_three_digits(self):
        """[table] "T7" normalizes to "T007"."""
        self.write_raw([raw_ticket("T7")])
        self.assertEqual(load_tickets(self.path)[0]["id"], "T007")

    def test_priority_disagreement_with_rules_is_preserved_not_recomputed(self):
        # §7 + §12.7 — stored priority is authoritative, never re-derived.
        # A hand-edited ticket whose priority disagrees with the current
        # urgency/affected_users rules loads UNCHANGED.
        t = raw_ticket(urgency="high", affected_users=12, priority="low")
        self.write_raw([t])
        loaded = load_tickets(self.path)
        self.assertEqual(loaded[0]["priority"], "low")



class SaveTicketsTests(StorageTestCase):

    def test_save_returns_none(self):
        """[§3] save_tickets is not a tuple-returning function."""
        self.assertIsNone(save_tickets([raw_ticket()], self.path))

    def test_save_creates_the_file(self):
        self.assertFalse(os.path.exists(self.path))
        save_tickets([raw_ticket()], self.path)
        self.assertTrue(os.path.exists(self.path))

    def test_save_creates_a_missing_parent_directory(self):
        """ASSUMPTION — the document does not mention the data/ directory.

        data/tickets.json is git-ignored, so on a fresh clone the directory is
        often absent. Making the writer create it keeps `main.py` from needing
        an os.makedirs call of its own.
        """
        nested = os.path.join(self.dir, "data", "tickets.json")
        save_tickets([raw_ticket()], nested)
        self.assertTrue(os.path.exists(nested))

    def test_save_overwrites_rather_than_appends(self):
        """Also catches a module-level buffer shared between calls: if one were
        reused, the second save would write T001 and T002, not just T002. The
        assertion is on the SECOND call because that is the first one that can
        show it — same failure mode as build_report's template dict.

        There is deliberately no separate "saves do not share state" test. It
        would make the same assertion on the same two calls.
        """
        save_tickets([raw_ticket("T001")], self.path)
        save_tickets([raw_ticket("T002")], self.path)
        self.assertEqual([t["id"] for t in self.read_raw()], ["T002"])

    def test_written_file_is_plain_json(self):
        """[§4] "json.dump(tickets, ...) writes the live list directly" — so the
        file must be a JSON array of objects, readable by anything."""
        save_tickets([raw_ticket()], self.path)
        with open(self.path, encoding="utf-8") as handle:
            self.assertIsInstance(json.load(handle), list)


class StorageIntegrationTests(StorageTestCase):
    """The boundary, end to end.

    §2 exists so that a broken file stops at load_tickets. These assert the
    consequence: the queue never sees a ticket it would have to guess about.
    """

    def test_corrupt_store_never_reaches_the_queue(self):
        """The payoff of §2's boundary rule, stated as a consequence.

        work_queue does RANK[t["priority"]] with no guard, on the assumption
        that the boundary already checked. If load_tickets passed a bad priority
        through, that KeyError is what the user would see — with a traceback
        pointing into reports.py, not at the file that is actually wrong.
        """
        self.write_raw([raw_ticket("T001", priority="urgent")])
        with self.assertRaises(CorruptDataError):
            load_tickets(self.path)

    def test_a_clean_store_survives_a_full_round_trip(self):
        """Save, reload, and queue — the three modules together."""
        try:
            from campusflow.reports import work_queue
        except ImportError:
            self.skipTest("campusflow.reports not available on this branch yet")


        tickets = [
            raw_ticket("T001", priority="low"),
            raw_ticket("T002", priority="critical"),
            raw_ticket("T003", priority="critical"),
        ]
        save_tickets(tickets, self.path)

        queued = [t["id"] for t in work_queue(load_tickets(self.path))]

        self.assertEqual(queued, ["T002", "T003", "T001"])

    def test_reloaded_priority_is_not_re_derived(self):
        """[table] "priority doesn't match what urgency+users would compute ->
        Trust the stored value (don't repair)." Originally written here as
        INFERRED from §7.

        The ticket below would compute to "low" and is stored as "critical". It
        must come back unchanged, because repairing it here would create the
        second source of truth §7 exists to prevent — the queue and the report
        could then disagree about the same ticket.
        """
        self.write_raw([raw_ticket(urgency="low", affected_users=1, priority="critical")])
        self.assertEqual(load_tickets(self.path)[0]["priority"], "critical")


if __name__ == "__main__":
    unittest.main()

class NotesStorageTests(StorageTestCase):
    """Tests for the CampusFlow Next notes and was_reopened schema (§12.7, §12.9)."""

    def _write(self, tickets):
        """Write a list of ticket dicts to a temp file, return the path."""
        import json
        with open(self.path, "w") as f:
            json.dump(tickets, f)
        return self.path

    def _ticket(self, **overrides):
        """Base ticket with notes and was_reopened. Override any field."""
        base = {
            "id": "T001",
            "title": "Wi-Fi down",
            "category": "Network",
            "urgency": "high",
            "affected_users": 12,
            "priority": "critical",
            "status": "open",
            "assigned_to": None,
            "notes": [],
            "was_reopened": False,
        }
        base.update(overrides)
        return base

    # --- was_reopened legacy compatibility (§12.9 exception) ---

    def test_legacy_ticket_without_was_reopened_loads_as_false(self):
        # §12.9: a missing was_reopened key is legacy data, default to False.
        # This is a DELIBERATE exception to §2's "missing key = raise" rule.
        legacy = self._ticket()
        del legacy["was_reopened"]
        loaded = load_tickets(self._write([legacy]))
        self.assertEqual(loaded[0]["was_reopened"], False)

    def test_was_reopened_true_loads_unchanged(self):
        loaded = load_tickets(self._write([self._ticket(was_reopened=True)]))
        self.assertIs(loaded[0]["was_reopened"], True)

    def test_non_bool_was_reopened_raises(self):
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(was_reopened="yes")]))

    # --- notes validation (§12.7) ---

    def test_empty_notes_list_loads_cleanly(self):
        loaded = load_tickets(self._write([self._ticket(notes=[])]))
        self.assertEqual(loaded[0]["notes"], [])

    def test_valid_note_loads_cleanly(self):
        note = {"note_id": "N001", "author": "Mentor A",
                "message": "Wi-Fi router reboot attempted"}
        loaded = load_tickets(self._write([self._ticket(notes=[note])]))
        self.assertEqual(len(loaded[0]["notes"]), 1)
        self.assertEqual(loaded[0]["notes"][0]["note_id"], "N001")

    def test_note_missing_note_id_raises(self):
        bad_note = {"author": "Mentor A", "message": "Wi-Fi router reboot attempted"}
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(notes=[bad_note])]))

    def test_note_id_wrong_prefix_raises(self):
        bad_note = {"note_id": "X001", "author": "Mentor A",
                    "message": "Wi-Fi router reboot attempted"}
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(notes=[bad_note])]))

    def test_duplicate_note_ids_within_a_ticket_raise(self):
        notes = [
            {"note_id": "N001", "author": "A", "message": "first message here"},
            {"note_id": "N001", "author": "B", "message": "second message here"},
        ]
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(notes=notes)]))

    def test_note_with_blank_author_raises(self):
        bad_note = {"note_id": "N001", "author": "   ",
                    "message": "Wi-Fi router reboot attempted"}
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(notes=[bad_note])]))

    def test_note_with_short_message_raises(self):
        bad_note = {"note_id": "N001", "author": "A", "message": "abc"}
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(notes=[bad_note])]))

    def test_note_with_long_message_raises(self):
        bad_note = {"note_id": "N001", "author": "A", "message": "x" * 301}
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(notes=[bad_note])]))

    def test_notes_field_missing_raises(self):
        # notes is a NEW required field (unlike was_reopened).
        # A ticket without notes is corrupt, not legacy.
        legacy = self._ticket()
        del legacy["notes"]
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([legacy]))

    def test_notes_field_not_a_list_raises(self):
        with self.assertRaises(CorruptDataError):
            load_tickets(self._write([self._ticket(notes="not a list")]))

    # --- Round-trip ---

    def test_save_and_load_preserves_notes_and_was_reopened(self):
        note = {"note_id": "N001", "author": "Mentor A",
                "message": "Wi-Fi router reboot attempted"}
        ticket = self._ticket(notes=[note], was_reopened=True)
        save_tickets([ticket], self.path)
        loaded = load_tickets(self.path)
        self.assertEqual(len(loaded[0]["notes"]), 1)
        self.assertEqual(loaded[0]["notes"][0]["note_id"], "N001")
        self.assertIs(loaded[0]["was_reopened"], True)