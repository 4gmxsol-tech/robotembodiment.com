#!/usr/bin/env python3
"""Regression checks for the robotic manipulation topic hub."""
from html.parser import HTMLParser
from pathlib import Path
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PAGE = ROOT / "robot-manipulation.html"
SITEMAP = ROOT / "sitemap.xml"
PAGE_URL = "https://robotembodiment.com/robot-manipulation.html"
HOME_URL = "https://robotembodiment.com/"
ARTICLE_URL = "https://robotembodiment.com/articles/robot-manipulation-explained.html"
EXPECTED_TITLE = "Robotic Manipulation Guide | Robot Embodiment"
EXPECTED_DESCRIPTION = "Explore robotic manipulation: grasping, object handling, motion planning, contact-aware control and practical evaluation for physical robot tasks."

class HubParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = []
        self.h1 = []
        self.in_title = False
        self.in_h1 = False
        self.in_jsonld = False
        self.jsonld = []
        self.meta = {}
        self.canonical = ""
        self.links = []
        self.visible = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "h1":
            self.in_h1 = True
            self.h1.append("")
        elif tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.meta[key.casefold()] = attrs.get("content", "")
        elif tag == "link" and attrs.get("rel", "").casefold() == "canonical":
            self.canonical = attrs.get("href", "")
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        elif tag == "script" and attrs.get("type") == "application/ld+json":
            self.in_jsonld = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag == "h1":
            self.in_h1 = False
        elif tag == "script":
            self.in_jsonld = False

    def handle_data(self, data):
        self.visible.append(data)
        if self.in_title:
            self.title.append(data)
        if self.in_h1 and self.h1:
            self.h1[-1] += data
        if self.in_jsonld:
            self.jsonld.append(data)

html = PAGE.read_text(encoding="utf-8")
parser = HubParser()
parser.feed(html)
title = " ".join("".join(parser.title).split())
description = parser.meta.get("description", "").strip()
visible = " ".join(" ".join(parser.visible).split())

assert title == EXPECTED_TITLE, f"Unexpected title: {title}"
assert 120 <= len(description) <= 160, f"Description length is {len(description)}"
assert description == EXPECTED_DESCRIPTION, "Meta description changed without updating the regression expectation"
assert parser.meta.get("og:title") == title, "Open Graph title must match the document title"
assert parser.meta.get("twitter:title") == title, "Twitter title must match the document title"
assert parser.meta.get("og:description") == description, "Open Graph description must match"
assert parser.meta.get("twitter:description") == description, "Twitter description must match"
assert parser.canonical == PAGE_URL, "Canonical must point to the hub URL"
assert parser.h1 == ["Robotic manipulation"], f"Expected one descriptive H1, found {parser.h1}"
assert "robotic manipulation" in visible.casefold()
assert "contact-aware execution" in visible.casefold()
assert "repeated trials" in visible.casefold()
assert ARTICLE_URL.replace("https://robotembodiment.com/", "") in parser.links, "Hub must link to the full technical guide"

schema = json.loads("".join(parser.jsonld))
assert schema.get("@type") == "WebPage"
assert schema.get("name") == "Robotic Manipulation Guide"
assert schema.get("url") == PAGE_URL
assert schema.get("description") == description
breadcrumb = schema.get("breadcrumb", {})
assert breadcrumb.get("@type") == "BreadcrumbList"
assert [(item.get("name"), item.get("item")) for item in breadcrumb.get("itemListElement", [])] == [
    ("Home", HOME_URL),
    ("Articles", "https://robotembodiment.com/articles.html"),
    ("Robotic manipulation", PAGE_URL),
]
assert 'aria-label="Breadcrumb"' in html
assert 'aria-current="page"' in html

root = ET.parse(SITEMAP)
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
entries = {
    node.findtext("sm:loc", default="", namespaces=ns):
    node.findtext("sm:lastmod", default="", namespaces=ns)
    for node in root.findall("sm:url", ns)
}
assert entries.get(PAGE_URL) == "2026-11-11", "Hub sitemap lastmod must match the update date"
assert entries.get(HOME_URL) == "2026-11-10", "Homepage sitemap lastmod must reflect the 10 November discovery-link update"
assert ARTICLE_URL in entries, "The linked full guide must remain in the sitemap"

ARTICLE_INDEX = ROOT / "articles.html"
index_html = ARTICLE_INDEX.read_text(encoding="utf-8")
card_start = index_html.index('<div class="ey">Manipulation</div>')
card_end = index_html.index("</article>", card_start)
card = index_html[card_start:card_end]
assert 'href="robot-manipulation.html"' in card, "Articles index must link to the manipulation topic hub"
assert "Explore manipulation topic hub" in card, "Hub link must have descriptive anchor text"
assert 'href="articles/robot-manipulation-explained.html"' in card, "Full technical guide link must remain"

HOME = ROOT / "index.html"
home_html = HOME.read_text(encoding="utf-8")
assert 'href="robot-manipulation.html">Robotic Manipulation Overview</a>' in home_html, "Homepage must expose a direct, descriptive link to the manipulation topic hub"

print("PASS: homepage and hub sitemap lastmod, article-index discovery link, guide link and homepage link")
