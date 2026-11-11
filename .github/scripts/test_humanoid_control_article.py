#!/usr/bin/env python3
"""Regression checks for the humanoid robot control article's SEO and markup."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "articles" / "humanoid-robot-control.html"
LISTING = ROOT / "articles.html"
SITEMAP = ROOT / "sitemap.xml"
PAGE_URL = "https://robotembodiment.com/articles/humanoid-robot-control.html"
EXPECTED_DATE = "2026-11-11"
EXPECTED_SITEMAP_DATE = "2026-11-11"

class StructureParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1_count = 0
        self.p_open = False
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.h1_count += 1
        if tag == "p":
            if self.p_open:
                self.errors.append("nested paragraph")
            self.p_open = True
        elif tag in {"h1", "h2", "h3", "section", "article", "ul", "ol", "div"} and self.p_open:
            self.errors.append(f"<{tag}> opened before the paragraph closed")

    def handle_endtag(self, tag):
        if tag == "p":
            if not self.p_open:
                self.errors.append("closing paragraph without an open paragraph")
            self.p_open = False

article = ARTICLE.read_text(encoding="utf-8")
listing = LISTING.read_text(encoding="utf-8")
sitemap = SITEMAP.read_text(encoding="utf-8")

assert article.count('<link rel="canonical" href="' + PAGE_URL + '">') == 1
assert "Humanoid Robot Control: Motion, Balance &amp; Whole-Body Control" in article
assert "humanoid robot control" in article.lower()
assert "humanoid motion control" in article.lower()
assert "joint control" in article.lower()
assert "Humanoid robot control stack at a glance" in article
for layer in ("Task and behavior planning", "Motion planning", "Whole-body control", "Joint and actuator control"):
    assert layer in article, f"Control stack layer is missing: {layer}"
assert "Cross-cutting state estimation and feedback" in article
assert "What is humanoid robot joint control" in article
assert "What is humanoid robot posture control?" in article

# Search Console shows "humanoid motion control" as a material query for this page.
meta_description = re.search(r'<meta name="description" content="([^"]+)">', article)
og_description = re.search(r'<meta property="og:description" content="([^"]+)">', article)
assert meta_description, "Meta description is missing"
assert og_description, "Open Graph description is missing"
description = meta_description.group(1)
assert 120 <= len(description) <= 160, f"Meta description must be 120-160 characters (got {len(description)})"
assert "humanoid robot control" in description.lower()
assert "humanoid motion control" in description.lower()
assert "<title>Humanoid Robot Control &amp; Motion Control: Balance &amp; Joint Guide</title>" in article, "Document title must target both verified control queries"
assert og_description.group(1) == description, "Open Graph description must match the search meta description"

schema_match = re.search(r'<script type="application/ld\+json">(.*?)</script>', article, re.S)
assert schema_match, "Article JSON-LD is missing"
schema = json.loads(schema_match.group(1))
assert schema.get("@type") == "Article"
assert schema.get("dateModified") == EXPECTED_DATE

json_ld_documents = []
for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', article, re.S):
    try:
        json_ld_documents.append(json.loads(raw))
    except json.JSONDecodeError as error:
        raise AssertionError(f"Invalid JSON-LD block: {error}") from error
breadcrumb = next((doc for doc in json_ld_documents if doc.get("@type") == "BreadcrumbList"), None)
assert breadcrumb is not None, "BreadcrumbList JSON-LD is missing"
expected_breadcrumbs = [
    {"position": 1, "name": "Home", "item": "https://robotembodiment.com/"},
    {"position": 2, "name": "Articles", "item": "https://robotembodiment.com/articles.html"},
    {"position": 3, "name": "Humanoid Robot Control", "item": PAGE_URL},
]
actual_breadcrumbs = [
    {"position": item.get("position"), "name": item.get("name"), "item": item.get("item")}
    for item in breadcrumb.get("itemListElement", [])
]
assert actual_breadcrumbs == expected_breadcrumbs, "BreadcrumbList must match the canonical Home > Articles > article hierarchy"
assert '<nav class="article-meta" aria-label="Breadcrumb">' in article
assert '<span aria-current="page">Humanoid Robot Control</span>' in article

visible_date = re.search(r"Updated ([A-Z][a-z]+ \d{1,2}, \d{4})", article)
assert visible_date, "Visible updated date is missing"
assert visible_date.group(1) == "November 11, 2026"

parser = StructureParser()
parser.feed(article)
assert parser.h1_count == 1, f"Expected one H1, found {parser.h1_count}"
assert not parser.p_open, "Unclosed paragraph"
assert not parser.errors, "; ".join(parser.errors)

root = ET.fromstring(sitemap)
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
entry = next((u for u in root.findall("sm:url", ns)
              if u.findtext("sm:loc", namespaces=ns) == PAGE_URL), None)
assert entry is not None, "Article is missing from sitemap"
assert entry.findtext("sm:lastmod", namespaces=ns) == EXPECTED_SITEMAP_DATE

assert "articles/humanoid-robot-control.html" in listing
assert "Humanoid Robot Control: Motion, Balance &amp; Whole-Body Control" in listing

print("PASS: canonical, title/intent, Article and BreadcrumbList JSON-LD, accessible breadcrumb, visible/schema date, sitemap, listing card and paragraph structure")
