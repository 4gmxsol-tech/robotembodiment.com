#!/usr/bin/env python3
"""Regression checks for the robotic manipulation topic hub."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "robot-manipulation.html"
SITEMAP = ROOT / "sitemap.xml"
URL = "https://robotembodiment.com/robot-manipulation.html"

html = PAGE.read_text(encoding="utf-8")
sitemap = SITEMAP.read_text(encoding="utf-8")
errors = []

canonical = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html, re.I)
if not canonical or canonical.group(1) != URL:
    errors.append("Manipulation hub canonical must remain self-referencing")

breadcrumb = re.search(
    r'<nav\b(?=[^>]*aria-label="Breadcrumb")[^>]*>(.*?)</nav>',
    html,
    re.I | re.S,
)
if not breadcrumb:
    errors.append("Visible accessible breadcrumb navigation is required")
else:
    body = breadcrumb.group(1)
    for href in ('href="index.html"', 'href="articles.html"'):
        if href not in body:
            errors.append(f"Breadcrumb parent link is missing: {href}")
    if '<span aria-current="page">Robotic manipulation</span>' not in body:
        errors.append("Current breadcrumb item must be exposed as the page")

if not re.search(r'\.breadcrumbs\s*\{[^}]*flex-wrap:\s*wrap', html, re.I | re.S):
    errors.append("Breadcrumbs must wrap on narrow screens")
if "a:focus-visible" not in html:
    errors.append("Breadcrumb links must retain a visible keyboard focus style")

task_section = re.search(
    r'<section\b(?=[^>]*aria-labelledby="task-patterns")[^>]*>(.*?)</section>',
    html,
    re.I | re.S,
)
if not task_section:
    errors.append("A labelled manipulation task-pattern section is required")
else:
    task_html = task_section.group(1)
    task_cards = re.findall(r'<article\s+class="card task-card">', task_html, re.I)
    if len(task_cards) != 4:
        errors.append(f"Expected four responsive manipulation task cards, found {len(task_cards)}")
    for phrase in (
        "Pick and place",
        "Insertion and assembly",
        "Pushing and sliding",
        "Tool use and bimanual work",
        "placement error",
        "peak contact force",
        "contact stability",
        "operator intervention",
    ):
        if phrase.casefold() not in task_html.casefold():
            errors.append(f"Manipulation task guidance is missing: {phrase}")

if not re.search(r'\.task-grid\s*\{[^}]*display:\s*grid', html, re.I | re.S):
    errors.append("Manipulation task cards must use a responsive grid")
if not re.search(r'@media\s*\(max-width:\s*640px\)[\s\S]*?\.task-grid\s*\{[^}]*grid-template-columns:\s*1fr', html, re.I):
    errors.append("Manipulation task cards must stack into one column on mobile")

schema_blocks = re.findall(
    r'<script\s+type="application/ld\+json">(.*?)</script>',
    html,
    re.I | re.S,
)
webpage_schemas = []
for block in schema_blocks:
    try:
        data = json.loads(block)
    except json.JSONDecodeError:
        continue
    if data.get("@type") == "WebPage":
        webpage_schemas.append(data)

if len(webpage_schemas) != 1:
    errors.append("Exactly one WebPage JSON-LD block is required")
else:
    items = webpage_schemas[0].get("breadcrumb", {}).get("itemListElement", [])
    expected = [
        ("Home", "https://robotembodiment.com/"),
        ("Articles", "https://robotembodiment.com/articles.html"),
        ("Robotic manipulation", URL),
    ]
    actual = [(item.get("name"), item.get("item")) for item in items]
    if webpage_schemas[0].get("breadcrumb", {}).get("@type") != "BreadcrumbList" or actual != expected:
        errors.append("WebPage breadcrumb schema must match the visible path")

for path in ("index.html", "articles.html"):
    page = (ROOT / path).read_text(encoding="utf-8")
    if 'href="robot-manipulation.html"' not in page:
        errors.append(f"{path} must keep an internal link to the manipulation hub")

entry = re.search(
    r'<url>\s*<loc>' + re.escape(URL) + r'</loc>\s*<lastmod>2026-11-11</lastmod>\s*</url>',
    sitemap,
    re.I | re.S,
)
if not entry:
    errors.append("Sitemap must keep the hub URL and reflect its 2026-11-11 content update")

if errors:
    raise SystemExit("\n".join(f"FAIL: {error}" for error in errors))

print("Manipulation hub breadcrumbs, schema, internal links and sitemap: PASS")
