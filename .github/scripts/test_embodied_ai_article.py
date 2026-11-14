#!/usr/bin/env python3
"""Regression checks for the embodied AI guide's content, SEO and internal links."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ARTICLE = ROOT / "articles" / "what-is-embodied-ai.html"
LISTING = ROOT / "articles.html"
SITEMAP = ROOT / "sitemap.xml"
PAGE_URL = "https://robotembodiment.com/articles/what-is-embodied-ai.html"
EXPECTED_DATE = "2026-11-14"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = []
        self.hrefs = []
        self.title = []
        self.in_title = False
        self.in_h1 = False
        self.paragraph_open = False
        self.errors = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1.append("")
            self.in_h1 = True
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])
        if tag == "title":
            self.in_title = True
        if tag == "p":
            if self.paragraph_open:
                self.errors.append("nested paragraph")
            self.paragraph_open = True
        elif tag in {"h1", "h2", "h3", "section", "article", "ul", "ol", "div"} and self.paragraph_open:
            self.errors.append(f"<{tag}> opened before paragraph closed")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        if tag == "h1":
            self.in_h1 = False
        if tag == "p":
            if not self.paragraph_open:
                self.errors.append("closing paragraph without open paragraph")
            self.paragraph_open = False

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if self.in_h1 and self.h1:
            self.h1[-1] += data

article = ARTICLE.read_text(encoding="utf-8")
listing = LISTING.read_text(encoding="utf-8")
sitemap = SITEMAP.read_text(encoding="utf-8")

parser = PageParser()
parser.feed(article)
assert len(parser.h1) == 1, f"Expected one H1, found {len(parser.h1)}"
assert parser.h1[0].strip() == "What Is Embodied AI?"
assert not parser.paragraph_open, "Unclosed paragraph"
assert not parser.errors, "; ".join(parser.errors)

title = "".join(parser.title).strip()
assert 30 <= len(title) <= 60, f"SEO title length is {len(title)}"
description_match = re.search(r'<meta name="description" content="([^"]+)"', article)
assert description_match, "Meta description missing"
description = description_match.group(1)
assert 120 <= len(description) <= 160, f"Meta description length is {len(description)}"

canonical = re.search(r'<link rel="canonical" href="([^"]+)"', article)
assert canonical and canonical.group(1) == PAGE_URL
schema_match = re.search(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', article, re.S)
assert schema_match, "Article JSON-LD missing"
schema = json.loads(schema_match.group(1))
assert schema.get("@type") == "Article"
assert schema.get("datePublished") == "2026-09-26"
assert schema.get("dateModified") == EXPECTED_DATE
assert schema.get("mainEntityOfPage") == PAGE_URL

assert "Updated November 14, 2026" in article

benchmark_url = "https://humanoidbehavior.com/benchmark.html"
benchmark_section = re.search(
    r'<section class="benchmark-referral"[^>]*>(.*?)</section>',
    article,
    re.S,
)
assert benchmark_section, "Embodied AI guide must provide a contextual benchmark referral"
benchmark_html = benchmark_section.group(1)
assert benchmark_html.count('href="' + benchmark_url + '"') == 1, "Benchmark referral must contain one clear destination"
for phrase in (
    "measured MuJoCo evaluations",
    "explicit seeds and policy versions",
    "stored with its configuration and results",
    "do not replace validation on the target robot",
):
    assert phrase.casefold() in benchmark_html.casefold(), f"Benchmark referral must preserve accurate scope: {phrase}"
assert 'rel="noopener noreferrer"' in benchmark_html, "External benchmark link must use safe relationship attributes"
assert article.index("<h2>Simulation, sim-to-real transfer and evaluation</h2>") < article.index('<section class="benchmark-referral"') < article.index("<h2>Embodied AI vs. physical AI vs. embodied intelligence</h2>"), "Benchmark referral must follow the evaluation section"
for phrase in (
    "perception", "decision-making", "execution and feedback",
    "vision-language-action", "cross-embodiment", "sim-to-real",
    "real-world evaluation", "physical constraints"
):
    assert phrase in article.lower(), f"Missing core topic: {phrase}"

word_count = len(re.findall(r"\b[\w'-]+\b", re.sub(r"<[^>]+>", " ", article)))
assert word_count >= 1000, f"Guide is too short ({word_count} words)"

for source in (
    "https://doi.org/10.1145/3717059",
    "https://doi.org/10.1002/smb2.70003",
    "https://arxiv.org/abs/2406.09246",
    "https://arxiv.org/abs/2310.08864",
    "https://arxiv.org/abs/2307.15818",
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

assert 'href="articles/what-is-embodied-ai.html"' in listing
assert "Definition, perception-to-action loop, VLA models, datasets, simulation and evaluation." in listing
comparison_path = ROOT / "articles" / "embodied-intelligence-vs-ai.html"
comparison_url = "https://robotembodiment.com/articles/embodied-intelligence-vs-ai.html"
comparison = comparison_path.read_text(encoding="utf-8")
assert comparison_url in urls, "Embodied intelligence comparison must remain in the sitemap"
assert '<h1>Embodied Intelligence vs Artificial Intelligence</h1>' in comparison
assert 'href="articles/embodied-intelligence-vs-ai.html"' in listing, "Article archive must link to the comparison guide"
assert 'href="embodied-intelligence-vs-ai.html"' in article, "Embodied AI guide must link contextually to the comparison guide"
assert urls.get("https://robotembodiment.com/articles.html") == "2026-11-14", "Article archive sitemap lastmod must match its new internal link"

print(f"PASS: {word_count} words; title/description; Article schema; visible date; sitemap; {len(parser.hrefs)} links; research references")
