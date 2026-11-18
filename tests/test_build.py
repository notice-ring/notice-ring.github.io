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
        earlier = dict(self.note, slug="earlier", date="2026-11-01", category="Learning")
        draft = dict(self.note, slug="draft", draft=True)
        result = self.load([earlier, draft, self.note])
        self.assertEqual([n["slug"] for n in result], ["first-note", "earlier"])

    def test_rejects_path_traversal_duplicates_and_invalid_dates(self):
        for notes in ([dict(self.note, slug="../../private")], [self.note, self.note],
                      [dict(self.note, date="2026-02-30")], [dict(self.note, draft="false")]):
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
