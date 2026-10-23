import unittest
import prepare_package_files as p

BASE = "https://github.com/Beneficial-Strategies/iso-20022-primitives"
RAW = "https://raw.githubusercontent.com/Beneficial-Strategies/iso-20022-primitives"


class Readme(unittest.TestCase):
    def test_it_is_cut_at_the_marker_and_the_snippet_markers_go(self):
        text = f"# T\n<!-- snippet: a#b -->\n```csharp\nx\n```\n<!-- /snippet -->\n{p.END_MARKER}\n## Building\n"
        out = p.package_readme(text, "1.0.0-alpha", "Beneficial-Strategies/iso-20022-primitives")
        self.assertNotIn("Building", out)
        self.assertNotIn("snippet", out)
        self.assertIn("```csharp\nx\n```", out)

    def test_links_to_main_are_pinned_to_the_tag(self):
        text = f"![x]({RAW}/main/.beneficial/logo.png)\n[p]({BASE}/tree/main/examples/01)\n{p.END_MARKER}\n"
        out = p.package_readme(text, "1.0.0-alpha", "Beneficial-Strategies/iso-20022-primitives")
        self.assertIn(f"{RAW}/v1.0.0-alpha/.beneficial/logo.png", out)
        self.assertIn(f"{BASE}/tree/v1.0.0-alpha/examples/01", out)
        self.assertEqual([], p.problems(out))

    def test_the_notice_of_the_template_is_not_packed(self):
        text = f"<!-- template-notice -->\n> see [x](.template/a.md)\n<!-- /template-notice -->\n\n# T\n{p.END_MARKER}\n"
        out = p.package_readme(text, "1.0.0", "o/r")
        self.assertNotIn("template", out)
        self.assertEqual([], p.problems(out))

    def test_a_missing_marker_fails(self):
        with self.assertRaises(SystemExit):
            p.package_readme("# T\n", "1.0.0", "o/r")


class Problems(unittest.TestCase):
    def test_relative_links_and_images_are_found(self):
        self.assertEqual(2, len(p.problems("[a](docs/a.md) ![b](img/b.png)")))

    def test_an_image_from_another_domain_is_found(self):
        self.assertEqual(1, len(p.problems("![b](https://beneficialstrategies.com/img/logo.svg)")))
        self.assertEqual([], p.problems(f"![b]({RAW}/v1.0.0/.beneficial/logo.png)"))

    def test_raw_html_and_braces_are_found_but_code_is_not_read(self):
        self.assertEqual(1, len(p.problems("<img src='x'>")))
        self.assertEqual(1, len(p.problems("version {{version}}")))
        self.assertEqual([], p.problems("```\n<b>[a](x) {{y}}\n```\nand `<i>`"))

    def test_an_unpinned_link_is_found(self):
        self.assertEqual(1, len(p.problems(f"[x]({BASE}/tree/main/examples)")))


class Changelog(unittest.TestCase):
    LOG = "# Changelog\n\n## 1.1.0-alpha (2026-10-23)\n\n* Added: a (#1).\n* Fixed: b (#2).\n\n## 1.0.0-alpha (2026-10-01)\n\nFirst.\n"

    def test_the_entry_is_plain_text_without_its_heading(self):
        self.assertEqual("Added: a (#1).\nFixed: b (#2).\n", p.changelog_entry(self.LOG, "1.1.0-alpha"))
        self.assertEqual("First.\n", p.changelog_entry(self.LOG, "1.0.0-alpha"))

    def test_a_version_without_an_entry_fails(self):
        with self.assertRaises(SystemExit):
            p.changelog_entry(self.LOG, "2.0.0")


if __name__ == "__main__":
    unittest.main()
