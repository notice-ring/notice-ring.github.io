"""Build a portable static homepage using only Python's standard library."""

import json
import argparse
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from string import Template

ROOT = Path(__file__).resolve().parent


def read_notes(path):
    notes = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(notes, list):
        raise ValueError("notes.json must contain a list")
    slugs = set()
    for note in notes:
        if not isinstance(note, dict):
            raise ValueError("Each note must be an object")
        slug = note.get("slug", "")
        if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ValueError(f"Invalid note slug: {slug!r}")
        if slug in slugs:
            raise ValueError(f"Duplicate note slug: {slug}")
        slugs.add(slug)
        for field in ("title", "date", "summary"):
            if not isinstance(note.get(field), str) or not note[field].strip():
                raise ValueError(f"{slug}: {field} must be nonempty text")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", note["date"]):
            raise ValueError(f"{slug}: date must use YYYY-MM-DD")
        date.fromisoformat(note["date"])
        if not isinstance(note.get("body"), list) or not all(isinstance(p, str) for p in note["body"]):
            raise ValueError(f"{slug}: body must be a list of paragraphs")
        if note.get("language", "en") not in ("en", "ko"):
            raise ValueError(f"{slug}: language must be en or ko")
        if not isinstance(note.get("draft", False), bool):
            raise ValueError(f"{slug}: draft must be a boolean")
        if note.get("category") is not None and not isinstance(note["category"], str):
            raise ValueError(f"{slug}: category must be text or null")
    return sorted((n for n in notes if not n.get("draft", False)), key=lambda n: n["date"], reverse=True)


def display_date(value):
    return date.fromisoformat(value).strftime("%b %d, %Y")


def render_note_list(notes):
    if not notes:
        return '<p class="empty-note">No notes published yet.</p>'
    rows = []
    for n in notes:
        rows.append(
            f'<li lang="{n.get("language", "en")}"><time class="date" datetime="{n["date"]}">{display_date(n["date"])}</time>'
            f'<h3><a href="note/{n["slug"]}.html">{escape(n["title"])}</a></h3>'
            f'<p>{escape(n["summary"])}</p></li>'
        )
    return '<ul class="note-list">' + "\n".join(rows) + "</ul>"


def build(output=None):
    output = Path(output) if output is not None else ROOT / "dist"
    notes = read_notes(ROOT / "content/notes.json")
    cv = ROOT / "static/assets/Jihwan_Gong_CV.pdf"
    if not cv.is_file():
        raise FileNotFoundError(f"CV missing: {cv}")
    template = Template((ROOT / "templates/index.html").read_text(encoding="utf-8"))
    note_template = Template((ROOT / "templates/note.html").read_text(encoding="utf-8"))
    # Render before touching output so invalid content never overwrites a working build.
    pages = {"index.html": template.substitute(note_list=render_note_list(notes))}
    for n in notes:
        pages[f'note/{n["slug"]}.html'] = note_template.substitute(
            language=n.get("language", "en"), title=escape(n["title"]),
            summary=escape(n["summary"], quote=True), date=n["date"],
            display_date=display_date(n["date"]),
            body="\n".join(f"<p>{escape(p)}</p>" for p in n["body"]),
        )
    output.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "static", output, dirs_exist_ok=True)
    # Only remove generated Note pages; drafts and removed articles must disappear.
    for old in (output / "note").glob("*.html"):
        old.unlink()
    for name, html in pages.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
    (output / ".nojekyll").touch()
    return output, len(notes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Output directory (default: dist)")
    folder, count = build(parser.parse_args().output)
    print(f"Built {folder} ({count} published notes)")
