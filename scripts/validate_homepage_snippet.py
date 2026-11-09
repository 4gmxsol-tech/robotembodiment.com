#!/usr/bin/env python3
"""Regression checks for the Robot Embodiment homepage search snippet."""
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
CANONICAL = "https://robotembodiment.com/"
REQUIRED_TERMS = ("robot embodiment", "morphology", "sensors", "kinematics", "control")
REQUIRED_VISIBLE_TEXT = (
    "Kinematics, sensors, action spaces and dynamics change the way intelligence "
    "reaches the physical world."
)

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.in_title = False
        self.meta = {}
        self.canonical = ""
        self.visible_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            key = attrs.get("name") or attrs.get("property")
            if key:
                self.meta[key.casefold()] = attrs.get("content", "")
        elif tag == "link" and attrs.get("rel", "").casefold() == "canonical":
            self.canonical = attrs.get("href", "")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        self.visible_parts.append(data)
        if self.in_title:
            self.title_parts.append(data)

def main():
    html = PAGE.read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(html)
    title = " ".join("".join(parser.title_parts).split())
    description = " ".join(parser.meta.get("description", "").split())
    visible_text = " ".join(" ".join(parser.visible_parts).split())
    errors = []

    if not 45 <= len(title) <= 65:
        errors.append(f"title length must be 45-65 characters (got {len(title)})")
    if not 120 <= len(description) <= 160:
        errors.append(f"meta description length must be 120-160 characters (got {len(description)})")
    if parser.meta.get("og:description", "").strip() != description:
        errors.append("Open Graph description must match the meta description")
    if parser.canonical != CANONICAL:
        errors.append("canonical URL must remain https://robotembodiment.com/")
    for term in REQUIRED_TERMS:
        if term not in description.casefold():
            errors.append(f"meta description is missing the query-relevant term: {term}")
    if REQUIRED_VISIBLE_TEXT.casefold() not in visible_text.casefold():
        errors.append("snippet claims must remain supported by the visible homepage explanation")

    sitemap = ET.parse(SITEMAP)
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    entry = next(
        (node for node in sitemap.findall("sm:url", namespace)
         if (node.findtext("sm:loc", default="", namespaces=namespace) == CANONICAL)),
        None,
    )
    if entry is None:
        errors.append("homepage canonical URL must remain present in the sitemap")
    else:
        lastmod = entry.findtext("sm:lastmod", default="", namespaces=namespace)
        try:
            date.fromisoformat(lastmod)
        except ValueError:
            errors.append("homepage sitemap lastmod must be a valid ISO date")

    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print(
        "PASS: homepage title, search snippet, Open Graph description, canonical, "
        "visible-content support and sitemap entry are consistent."
    )
    return 0

if __name__ == "__main__":
    sys.exit(main())
