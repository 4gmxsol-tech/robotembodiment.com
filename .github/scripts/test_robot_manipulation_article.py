#!/usr/bin/env python3
"""Regression checks for the robot manipulation guide."""
from html.parser import HTMLParser
from html import unescape
from pathlib import Path
from urllib.parse import urljoin
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "articles" / "robot-manipulation-explained.html"
LISTING = ROOT / "articles.html"
SITEMAP = ROOT / "sitemap.xml"
PAGE_URL = "https://robotembodiment.com/articles/robot-manipulation-explained.html"
EXPECTED_DATE = "2026-11-12"

class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = []
        self.in_h1 = False
        self.hrefs = []
        self.title = []
        self.in_title = False
        self.p_open = False
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1.append("")
            self.in_h1 = True
        elif tag == "title":
            self.in_title = True
        elif tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag == "p":
            if self.p_open:
                self.errors.append("nested paragraph")
            self.p_open = True
        elif tag in {"h1", "h2", "h3", "section", "article", "ul", "ol", "div"} and self.p_open:
            self.errors.append(f"<{tag}> opened before paragraph closed")

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_h1 = False
        elif tag == "title":
            self.in_title = False
        elif tag == "p":
            if not self.p_open:
                self.errors.append("closing paragraph without open paragraph")
            self.p_open = False

    def handle_data(self, data):
        if self.in_h1 and self.h1:
            self.h1[-1] += data
        if self.in_title:
            self.title.append(data)

article = ARTICLE.read_text(encoding="utf-8")
listing = LISTING.read_text(encoding="utf-8")
sitemap = SITEMAP.read_text(encoding="utf-8")

parser = ArticleParser()
parser.feed(article)
assert len(parser.h1) == 1, f"Expected one H1, found {len(parser.h1)}"
assert parser.h1[0].strip() == "Robot Manipulation Explained"
assert not parser.p_open, "Unclosed paragraph"
assert not parser.errors, "; ".join(parser.errors)

title = "".join(parser.title).strip()
assert 30 <= len(title) <= 60, f"SEO title length is {len(title)}"
description_match = re.search(r'<meta name="description" content="([^"]+)"', article)
assert description_match, "Meta description missing"
description = description_match.group(1)

og_title_match = re.search(r'<meta property="og:title" content="([^"]+)"', article)
twitter_title_match = re.search(r'<meta name="twitter:title" content="([^"]+)"', article)
og_description_match = re.search(r'<meta property="og:description" content="([^"]+)"', article)
twitter_description_match = re.search(r'<meta name="twitter:description" content="([^"]+)"', article)
assert og_title_match and unescape(og_title_match.group(1)) == title, "Open Graph title must match the document title"
assert twitter_title_match and unescape(twitter_title_match.group(1)) == title, "Twitter title must match the document title"
assert og_description_match and unescape(og_description_match.group(1)) == description, "Open Graph description must match the meta description"
assert twitter_description_match and unescape(twitter_description_match.group(1)) == description, "Twitter description must match the meta description"
assert "robotic manipulation" in title.lower(), "SEO title must include the Search Console phrase 'robotic manipulation'"
assert "robotic manipulation" in description.lower(), "Meta description must retain the Search Console phrase 'robotic manipulation'"
assert 120 <= len(description) <= 160, f"Meta description length is {len(description)}"

canonical = re.search(r'<link rel="canonical" href="([^"]+)"', article)
assert canonical and canonical.group(1) == PAGE_URL
schema_match = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', article, re.S)
assert schema_match, "Article JSON-LD missing"
schema = json.loads(schema_match.group(1))
assert schema.get("@type") == "Article"
assert schema.get("headline") == "Robotic Manipulation: Grasping, Planning and Control"
assert schema.get("datePublished") == "2026-09-26"
assert schema.get("dateModified") == EXPECTED_DATE
assert schema.get("mainEntityOfPage") == PAGE_URL
assert "Updated November 12, 2026" in article

for phrase in (
    "robot manipulation", "grasp planning", "contact sensing",
    "task planning", "motion planning", "feedback", "end effector",
    "impedance", "imitation learning", "cross-embodiment",
    "evaluation", "sim-to-real", "robot motion planning vs robotic manipulation",
    "free-space motion", "non-prehensile manipulation", "in-hand manipulation",
    "task-and-motion planning"
):
    assert phrase in article.lower(), f"Missing core topic: {phrase}"

word_count = len(re.findall(r"\b[\w'-]+\b", re.sub(r"<[^>]+>", " ", article)))
assert word_count >= 1100, f"Guide is too short ({word_count} words)"

for source in (
    "https://arxiv.org/abs/2403.12945",
    "https://arxiv.org/abs/2304.13705",
    "https://arxiv.org/abs/2303.04137",
    "https://arxiv.org/abs/2310.08864",
    "https://arxiv.org/abs/2401.02117",
    "https://doi.org/10.1146/annurev-control-060117-104848",
    "https://arxiv.org/abs/2112.01942",
):
    assert source in article, f"Missing research source: {source}"

root = ET.fromstring(sitemap)
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
urls = {}
for item in root.findall("sm:url", ns):
    loc = item.findtext("sm:loc", namespaces=ns)
    if loc:
        urls[loc] = item.findtext("sm:lastmod", namespaces=ns)
assert urls.get(PAGE_URL) == EXPECTED_DATE, "Sitemap lastmod is missing or stale"

broken = []
for href in parser.hrefs:
    if href.startswith(("https://", "http://", "mailto:", "tel:", "#")):
        continue
    resolved = urljoin(PAGE_URL, href.split("#", 1)[0])
    if resolved and resolved not in urls:
        broken.append(resolved)
assert not broken, "Internal links missing from sitemap: " + ", ".join(sorted(set(broken)))

assert 'href="articles/robot-manipulation-explained.html"' in listing
assert "Perception, grasp planning, contact sensing, motion control and robot learning for reliable physical interaction." in listing

aside_match = re.search(r'<aside class="article-aside".*?</aside>', article, re.S)
assert aside_match, "Related guides sidebar must remain present"
assert 'href="../robot-manipulation.html">Robotic manipulation overview</a>' in aside_match.group(0), "Related guides sidebar must link prominently to the robotic manipulation topic hub"

print(f"PASS: {word_count} words; title/description; Article schema; visible date; sitemap; {len(parser.hrefs)} links; seven research references")
