"""Build a portable static homepage using only Python's standard library."""

import json
import argparse
import re
import shutil
from datetime import date
from html import escape
from pathlib import Path
from posixpath import dirname, relpath
from string import Template
from textwrap import indent

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://notice-ring.github.io/"
PAGE_COPY = {
    "en": {
        "index.html": ("Home", "Jihwan Gong, SNU ECE undergraduate interested in Physical AI, including human-like learning, reasoning, and action, as well as Agentic Robotics."),
        "research.html": ("Research", "DiVE at CoRL 2026 and Jihwan Gong's research experience."),
        "community.html": ("Community", "Robotics education and teaching at SHAPE, Seoul National University."),
        "notes.html": ("Note", "Jihwan Gong's notes on research, building robots, and working alongside AI."),
    },
    "ko": {
        "index.html": ("홈", "Physical AI와 로봇의 학습·추론·행동을 공부하는 서울대학교 전기·정보공학부 공지환입니다."),
        "research.html": ("연구", "공지환의 CoRL 2026 논문 DiVE와 연구 경험입니다."),
        "community.html": ("활동", "서울대학교 동아리 SHAPE에서의 로봇 교육 활동입니다."),
        "notes.html": ("노트", "연구와 로봇 개발, AI와 함께 일하며 배운 점을 기록합니다."),
    },
}
INTERFACE_COPY = {
    "en": {"skip": "Skip to content", "nav_label": "Main navigation", "language_label": "Language", "email": "Email", "signature": "Jihwan Gong · Seoul"},
    "ko": {"skip": "본문으로 건너뛰기", "nav_label": "주 메뉴", "language_label": "언어 선택", "email": "이메일", "signature": "공지환 · 서울"},
}


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


def display_date(value, language):
    day = date.fromisoformat(value)
    if language == "ko":
        return f"{day.year}년 {day.month}월 {day.day}일"
    return day.strftime("%b %d, %Y")


def render_note_list(notes, language="en"):
    if not notes:
        message = "아직 공개된 글이 없습니다." if language == "ko" else "No notes published yet."
        return f'<p class="empty-note">{message}</p>'
    rows = []
    root = "../" if language == "ko" else ""
    for n in notes:
        rows.append(
            f'<li><time class="date" datetime="{n["date"]}">{display_date(n["date"], language)}</time>'
            f'<div lang="{n.get("language", "en")}"><h3><a href="{root}note/{n["slug"]}.html">{escape(n["title"])}</a></h3>'
            f'<p>{escape(n["summary"])}</p></div></li>'
        )
    return '<ul class="note-list">' + "\n".join(rows) + "</ul>"


def localized_path(page, language):
    return f"kr/{page}" if language == "ko" else page


def public_url(path):
    if path in ("index.html", "kr/index.html"):
        path = path.removesuffix("index.html")
    return SITE_URL + path


def render_page(layout, path, content, title, description, *, language):
    is_article = path.startswith("note/")
    is_home = path == localized_path("index.html", language)
    root = "../" if "/" in path else ""
    note_page = localized_path("notes.html", language)
    navigation = []
    for page, (label, _) in PAGE_COPY[language].items():
        target = localized_path(page, language)
        href = relpath(target, dirname(path) or ".")
        current = ""
        if target == path:
            current = ' aria-current="page"'
        elif is_article and target == note_page:
            current = ' aria-current="location"'
        navigation.append(f'      <a href="{href}"{current}>{label}</a>')

    equivalent_page = "notes.html" if is_article else path.rsplit("/", 1)[-1]
    language_links = []
    alternates = []
    for locale, label, name in (("en", "EN", "English"), ("ko", "KR", "한국어")):
        target = localized_path(equivalent_page, locale)
        if locale == language:
            language_links.append(f'<span lang="{locale}" aria-label="{name}" aria-current="true">{label}</span>')
        else:
            href = relpath(target, dirname(path) or ".")
            language_links.append(f'<a href="{href}" hreflang="{locale}" lang="{locale}" aria-label="{name}">{label}</a>')
        if not is_article:
            alternates.append(f'  <link rel="alternate" hreflang="{locale}" href="{public_url(target)}">')
    return layout.substitute(
        language=language,
        root=root,
        canonical=public_url(path),
        alternates="\n".join(alternates),
        title=escape(title, quote=True),
        description=escape(description, quote=True),
        page_type="article" if is_article else "website",
        home=relpath(localized_path("index.html", language), dirname(path) or "."),
        navigation="\n".join(navigation),
        language_switch='<span aria-hidden="true">/</span>'.join(language_links),
        main_class="note-page" if is_article else "home" if is_home else "page",
        content=indent(content.rstrip(), "    "),
        **INTERFACE_COPY[language],
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
    pages = {}
    for language, copies in PAGE_COPY.items():
        name = "공지환" if language == "ko" else "Jihwan Gong"
        for page, (label, description) in copies.items():
            path = localized_path(page, language)
            content = (templates / path).read_text(encoding="utf-8")
            if page == "notes.html":
                content = Template(content).substitute(note_list=render_note_list(notes, language))
            title = f"{name} · Physical AI" if page == "index.html" else f"{label} · {name}"
            pages[path] = render_page(layout, path, content, title, description, language=language)
    for n in notes:
        language = n.get("language", "en")
        path = f'note/{n["slug"]}.html'
        content = note_template.substitute(
            title=escape(n["title"]),
            summary=escape(n["summary"], quote=True), date=n["date"],
            display_date=display_date(n["date"], language),
            note_label=PAGE_COPY[language]["notes.html"][0],
            note_list_url="../" + localized_path("notes.html", language),
            body="\n".join(f"<p>{escape(p)}</p>" for p in n["body"]),
        )
        pages[path] = render_page(layout, path, content, f'{n["title"]} · Jihwan Gong', n["summary"], language=language)
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
