#!/usr/bin/env python3
"""Guard contextual links into the humanoid robot control topic cluster."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
TARGET = "humanoid-robot-control.html"
TARGET_PATH = ROOT / "articles" / TARGET
SITEMAP = ET.parse(ROOT / "sitemap.xml").getroot()
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
EXPECTED_LASTMOD = "2026-11-09"

class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href, " ".join(" ".join(self._text).split())))
            self._href = None
            self._text = []

assert TARGET_PATH.is_file(), "Humanoid robot control target page is missing"

expected = {
    "robot-embodiment-benchmark.html": "humanoid robot control",
    "robot-embodiment-gap.html": "humanoid robot control stack",
}
for source, phrase in expected.items():
    path = ROOT / "articles" / source
    assert path.is_file(), f"Source article is missing: {source}"
    html = path.read_text(encoding="utf-8")
    parser = Anchors()
    parser.feed(html)
    schema_blocks = re.findall(
        r'<script\\s+type=["\\']application/ld\\+json["\\']>(.*?)</script>',
        html, re.I | re.S
    )
    article_schema = next(
        (json.loads(block) for block in schema_blocks
         if json.loads(block).get("@type") == "Article"),
        None
    )
    assert article_schema is not None, f"{source} is missing Article JSON-LD"
    assert article_schema.get("datePublished") == "2026-10-06", (
        f"{source} original publication date must remain unchanged"
    )
    assert article_schema.get("dateModified") == EXPECTED_LASTMOD, (
        f"{source} Article dateModified must match the content update"
    )
    assert "Published October 6, 2026" in html
    assert "Updated November 9, 2026" in html

    matches = [(href, text) for href, text in parser.links if href == TARGET]
    assert len(matches) == 1, f"{source} must contain exactly one contextual control link"
    assert phrase in matches[0][1].lower(), f"{source} link anchor is not descriptive"
    assert "humanoid robot control" in matches[0][1].lower()

    url = f"https://robotembodiment.com/articles/{source}"
    entry = next((node for node in SITEMAP.findall("sm:url", NS)
                  if node.findtext("sm:loc", namespaces=NS) == url), None)
    assert entry is not None, f"{source} is missing from sitemap"
    assert entry.findtext("sm:lastmod", namespaces=NS) == EXPECTED_LASTMOD, (
        f"{source} sitemap lastmod must match the content update"
    )

print("PASS: contextual control-cluster links, descriptive anchors and sitemap freshness")
