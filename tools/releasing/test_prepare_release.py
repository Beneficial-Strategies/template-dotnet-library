import unittest
import prepare_release as r


def issue(n, title, *labels, body="", reason="COMPLETED"):
    return {"number": n, "title": title, "labels": [{"name": l} for l in labels], "body": body, "stateReason": reason}


class Bump(unittest.TestCase):
    def test_highest_label_wins(self):
        e = r.build_entries([issue(1, "a", "bug"), issue(2, "b", "enhancement"), issue(3, "c", "documentation")], {})
        self.assertEqual("compatible", r.choose_bump(e))
        e = r.build_entries([issue(1, "a", "bug"), issue(2, "b", "enhancement", "breaking-change")], {})
        self.assertEqual("breaking", r.choose_bump(e))
        e = r.build_entries([issue(1, "a", "breaking-change"), issue(2, "b", "redesign")], {})
        self.assertEqual("design", r.choose_bump(e))

    def test_everything_else_is_the_third_part(self):
        self.assertEqual("compatible", r.choose_bump(r.build_entries([issue(1, "a", "bug"), issue(2, "b", "documentation"), issue(3, "c", "enhancement")], {})))

    def test_a_raised_part_resets_the_ones_after_it_and_the_suffix_is_kept(self):
        self.assertEqual("1.2.4-alpha", r.next_version("1.2.3-alpha", "compatible"))
        self.assertEqual("1.3.0-alpha", r.next_version("1.2.3-alpha", "breaking"))
        self.assertEqual("2.0.0-alpha", r.next_version("1.2.3-alpha", "design"))
        self.assertEqual("1.0.1", r.next_version("1.0.0", "compatible"))

    def test_a_breaking_change_does_not_leave_the_first_part(self):
        self.assertEqual("1.1.0-alpha", r.next_version("1.0.0-alpha", "breaking"))


class Entries(unittest.TestCase):
    def test_not_planned_and_no_release_notes_are_left_out(self):
        e = r.build_entries([issue(1, "a", "bug", reason="NOT_PLANNED"), issue(2, "b", "bug", "no-release-notes"), issue(3, "c", "bug")], {})
        self.assertEqual([3], [x["number"] for x in e])

    def test_release_note_line_beats_the_title(self):
        e = r.build_entries([issue(5, "Title", "bug", body="x\nRelease note: Fixed the thing.\n")], {})
        self.assertEqual("Fixed the thing.", e[0]["text"])
        e = r.build_entries([issue(5, "Title", "bug", body="Release note: from issue")], {5: ["Release note: from the PR"]})
        self.assertEqual("from the PR", e[0]["text"])

    def test_empty_release_note_placeholder_falls_back_to_the_title(self):
        e = r.build_entries([issue(5, "Title", "bug")], {5: ["Release note:\n"]})
        self.assertEqual("Title", e[0]["text"])


class Render(unittest.TestCase):
    def test_entry_is_ordered_by_heading(self):
        e = r.build_entries([issue(2, "Fix thing", "bug"), issue(1, "New code set", "enhancement"), issue(3, "Rename", "breaking-change")], {})
        entry = r.render_entry("1.1.0-alpha", e, "2026-10-23")
        self.assertEqual(
            "## 1.1.0-alpha (2026-10-23)\n\n* Breaking change: Rename (#3).\n* Added: New code set (#1).\n* Fixed: Fix thing (#2).\n", entry)

    def test_the_new_entry_goes_above_the_previous_one(self):
        log = "# Changelog\n\nintro\n\n## 1.0.0-alpha (2026-10-01)\n\n* Added: a (#1).\n"
        out = r.add_entry(log, "## 1.0.1-alpha (2026-10-23)\n\n* Fixed: b (#2).\n")
        self.assertLess(out.index("1.0.1-alpha"), out.index("1.0.0-alpha"))
        self.assertTrue(out.startswith("# Changelog\n\nintro\n\n"))

    def test_version_is_replaced_in_the_props(self):
        self.assertEqual("<Version>1.1.0-alpha</Version>", r.set_version("<Version>1.0.0-alpha</Version>", "1.1.0-alpha"))


if __name__ == "__main__":
    unittest.main()
