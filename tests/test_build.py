import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build


class NotePublishingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        self.content = self.root / "notes.json"
        self.note = {"slug": "first-note", "title": "<script>alert(1)</script>",
                     "date": "2026-11-16", "summary": "Learning & building",
                     "body": ["<img src=x onerror=alert(1)>", "두 번째 문단"], "language": "ko"}

    def load(self, notes):
        self.content.write_text(json.dumps(notes), encoding="utf-8")
        return build.read_notes(self.content)

    def test_drafts_hidden_categories_optional_and_latest_first(self):
        earlier = dict(self.note, slug="earlier", date="2026-11-01", category="physical-ai-study")
        draft = dict(self.note, slug="draft", draft=True)
        result = self.load([earlier, draft, self.note])
        self.assertEqual([n["slug"] for n in result], ["first-note", "earlier"])

    def test_rejects_invalid_note_data(self):
        for notes in ([dict(self.note, slug="../../private")], [self.note, self.note],
                      [dict(self.note, date="2026-02-30")], [dict(self.note, draft="false")],
                      [dict(self.note, category="physical-ai-typo")]):
            with self.subTest(notes=notes), self.assertRaises(ValueError):
                self.load(notes)

    def test_empty_state_and_escaped_generated_pages(self):
        self.assertIn("No notes published yet", build.render_note_list([]))
        output = self.root / "dist"
        with patch.object(build, "read_notes", return_value=[self.note]):
            build.build(output)
        page = (output / "note/first-note.html").read_text()
        self.assertNotIn("<script>", page)
        self.assertNotIn("<img src=x", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn('lang="ko"', page)
        self.assertIn("두 번째 문단", page)
        self.assertIn('href="../kr/notes.html"', page)
        self.assertIn('href="../note/first-note.html"', (output / "kr/notes.html").read_text())
        self.assertTrue((output / "assets/Jihwan_Gong_CV.pdf").is_file())
        with patch.object(build, "read_notes", return_value=[]):
            build.build(output)
        self.assertFalse((output / "note/first-note.html").exists())

    def test_categories_group_published_notes_in_both_languages(self):
        output = self.root / "dist"
        entries = self.load([
            dict(self.note, category="ai-native"),
            dict(self.note, slug="build-note", category="build-log"),
            dict(self.note, slug="unpublished", category="physical-ai-study", draft=True),
        ])
        with patch.object(build, "read_notes", return_value=entries):
            build.build(output)
        for path in ("notes.html", "kr/notes.html"):
            with self.subTest(path=path):
                page = (output / path).read_text()
                for category, entry in (("ai-native", "first-note"), ("build-log", "build-note")):
                    section = page.split(f'id="{category}"', 1)[1].split("</section>", 1)[0]
                    self.assertIn(f"note/{entry}.html", section)
                    self.assertEqual(page.count(f"note/{entry}.html"), 1)
                self.assertIn('id="physical-ai-study"', page)
                self.assertNotIn("unpublished.html", page)
        self.assertIn('../kr/notes.html#ai-native', (output / "note/first-note.html").read_text())
        self.assertFalse((output / "note/unpublished.html").exists())

    def test_language_switch_links_to_the_same_section(self):
        output = self.root / "dist"
        with patch.object(build, "read_notes", return_value=[]):
            build.build(output)
        for section in ("index.html", "research.html", "community.html", "notes.html"):
            with self.subTest(section=section):
                english = (output / section).read_text()
                korean = (output / "kr" / section).read_text()
                self.assertIn('<html lang="en">', english)
                self.assertIn('<html lang="ko">', korean)
                self.assertIn(f'href="kr/{section}" hreflang="ko"', english)
                self.assertIn(f'href="../{section}" hreflang="en"', korean)
                self.assertIn(f'href="{section}" aria-current="page"', english)
                self.assertIn(f'href="{section}" aria-current="page"', korean)


if __name__ == "__main__":
    unittest.main()
