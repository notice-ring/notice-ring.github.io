"""Build a portable static homepage using only Python's standard library."""

import json
import argparse
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from string import Template
from textwrap import indent

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://notice-ring.github.io/"
SECTIONS = (
    ("research.html", "Research", "DiVE at CoRL 2026 and Jihwan Gong's research experience."),
    ("community.html", "Community", "Robotics education and teaching at SHAPE, Seoul National University."),
    ("notes.html", "Note", "Jihwan Gong's notes on research, building robots, and working alongside AI."),
)


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


def render_page(layout, path, content, title, description, *, language="en"):
    is_article = path.startswith("note/")
    is_home = path == "index.html"
    root = "../" if is_article else ""
    navigation = []
    for href, label, _ in SECTIONS:
        current = ""
        if href == path:
            current = ' aria-current="page"'
        elif is_article and href == "notes.html":
            current = ' aria-current="location"'
        navigation.append(f'      <a href="{root}{href}"{current}>{label}</a>')
    return layout.substitute(
        language=language,
        root=root,
        canonical=SITE_URL + ("" if is_home else path),
        title=escape(title, quote=True),
        description=escape(description, quote=True),
        page_type="article" if is_article else "website",
        home_current=' aria-current="page"' if is_home else "",
        navigation="\n".join(navigation),
        main_class="note-page" if is_article else "home" if is_home else "page",
        content=indent(content.rstrip(), "    "),
    )


def build(output=None):
    output = Path(output) if output is not None else ROOT / "dist"
    notes = read_notes(ROOT / "content/notes.json")
    cv = ROOT / "static/assets/Jihwan_Gong_CV.pdf"
    if not cv.is_file():
        raise FileNotFoundError(f"CV missing: {cv}")
    templates = ROOT / "templates"
    layout = Template((templates / "layout.html").read_text(encoding="utf-8"))
    note_template = Template((templates / "note.html").read_text(encoding="utf-8"))
    # Render before touching output so invalid content never overwrites a working build.
    pages = {"index.html": render_page(
        layout, "index.html", (templates / "index.html").read_text(encoding="utf-8"),
        "Jihwan Gong · Physical AI",
        "Jihwan Gong, SNU ECE undergraduate interested in Physical AI, including human-like learning, reasoning, and action, as well as Agentic Robotics.",
    )}
    for path, title, description in SECTIONS:
        content = (templates / path).read_text(encoding="utf-8")
        if path == "notes.html":
            content = Template(content).substitute(note_list=render_note_list(notes))
        pages[path] = render_page(layout, path, content, f"{title} · Jihwan Gong", description)
    for n in notes:
        path = f'note/{n["slug"]}.html'
        content = note_template.substitute(
            title=escape(n["title"]),
            summary=escape(n["summary"], quote=True), date=n["date"],
            display_date=display_date(n["date"]),
            body="\n".join(f"<p>{escape(p)}</p>" for p in n["body"]),
        )
        pages[path] = render_page(layout, path, content, f'{n["title"]} · Jihwan Gong', n["summary"], language=n.get("language", "en"))
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
