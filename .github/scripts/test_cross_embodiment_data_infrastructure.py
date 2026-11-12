#!/usr/bin/env python3
"""Regression checks for the cross-embodiment data collection guide."""
from html.parser import HTMLParser
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
ARTICLE_PATH = ROOT / "articles" / "cross-embodiment-robotics.html"
LISTING_PATH = ROOT / "articles.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
PAGE_URL = "https://robotembodiment.com/articles/cross-embodiment-robotics.html"
EXPECTED_MODIFIED = "2026-11-13"

class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.h1 = []
        self.in_h1 = False
        self.title = []
        self.in_title = False
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "h1":
            self.h1.append("")
            self.in_h1 = True
        elif tag == "title":
            self.in_title = True
        elif tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag == "h1":
            self.in_h1 = False
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data):
        self.text.append(data)
        if self.in_h1 and self.h1:
            self.h1[-1] += data
        if self.in_title:
            self.title.append(data)

article = ARTICLE_PATH.read_text(encoding="utf-8")
listing = LISTING_PATH.read_text(encoding="utf-8")
parser = PageParser()
parser.feed(article)

assert parser.h1 == ["Cross-Embodiment Robotics"], "The article must keep one clear H1"
title = "".join(parser.title).strip()
assert title == "Cross-Embodiment Data Collection and Infrastructure | Robot Embodiment"
assert 30 <= len(title) <= 70, "SEO title length is outside the target range"
description_match = re.search(r'<meta name="description" content="([^"]+)"', article)
assert description_match, "Meta description is missing"
description = description_match.group(1)
assert 120 <= len(description) <= 160, "Meta description length is outside the target range"
assert "cross-embodiment robotics data infrastructure" in description.lower(), "Meta description must match the verified data-infrastructure query intent"

for tag, value in (
    ("og:title", title),
    ("twitter:title", title),
    ("og:description", description),
    ("twitter:description", description),
):
    match = re.search(r'<meta (?:property|name)="' + re.escape(tag) + r'" content="([^"]+)"', article)
    assert match and match.group(1) == value, f"{tag} must match the document metadata"

schema_blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', article, re.I | re.S)
schemas = [json.loads(block) for block in schema_blocks]
article_schema = next((item for item in schemas if item.get("@type") == "Article"), None)
assert article_schema, "Article JSON-LD is missing"
assert article_schema.get("datePublished") == "2026-10-06", "Original publication date must remain unchanged"
assert article_schema.get("dateModified") == EXPECTED_MODIFIED, "Article dateModified must match the update"
assert article_schema.get("mainEntityOfPage") == PAGE_URL
assert article_schema.get("headline") == "Cross-Embodiment Data Collection and Infrastructure for Robotics"

visible_text = " ".join(parser.text)
assert "Published October 6, 2026" in visible_text
assert "Updated November 12, 2026" in visible_text
for phrase in (
    "cross-embodiment robotics data infrastructure",
    "cross-embodiment data collection",
    "embodiment profile",
    "synchronize observations and actions",
    "quality checks",
    "dataset release",
    "held-out target embodiments",
    "operator interventions",
):
    assert phrase in visible_text.lower(), f"Missing practical content: {phrase}"


manifest_match = re.search(
    r'<pre class="code-sample" id="dataset-manifest"><code>(.*?)</code></pre>',
    article,
    re.S,
)
assert manifest_match, "A machine-readable dataset manifest example must be present"
manifest = json.loads(manifest_match.group(1))
assert manifest.get("dataset_id") and manifest.get("version"), "Manifest must identify its dataset and version"
robot = manifest.get("robot", {})
assert robot.get("model", "").startswith("REPLACE_WITH_"), "Robot model must be an explicit placeholder, not an invented identifier"
assert robot.get("degrees_of_freedom") and robot.get("end_effector"), "Manifest must describe the embodiment"
assert {"base", "tool", "camera"}.issubset(set(robot.get("coordinate_frames", []))), "Manifest must name its coordinate frames"
assert manifest.get("task", {}).get("success_criteria"), "Manifest must state the task success criteria"
streams = manifest.get("streams", [])
stream_names = {stream.get("name") for stream in streams}
assert {"camera_rgb", "joint_state", "commanded_joint_position", "executed_joint_position"}.issubset(stream_names), "Manifest must distinguish observations and commanded/executed actions"
for stream in streams:
    assert stream.get("timestamp_clock") and stream.get("timestamp_unit"), "Each stream must declare its clock and timestamp unit"
for name in ("joint_state", "commanded_joint_position", "executed_joint_position"):
    stream = next(item for item in streams if item.get("name") == name)
    assert stream.get("units") == "rad", f"{name} must declare its units"
provenance = manifest.get("provenance", {})
assert provenance.get("source", "").startswith("REPLACE_WITH_"), "Collection source must not be fabricated"
assert provenance.get("license", "").startswith("REPLACE_WITH_"), "Dataset license must not be fabricated"
assert provenance.get("consent_record", "").startswith("REPLACE_WITH_"), "Consent evidence must not be fabricated"
assert "illustrative manifest, not a universal schema" in article.lower(), "The example must be clearly labeled as illustrative"
assert "document the synchronization mapping" in article.lower(), "The article must explain clock synchronization for mixed streams"

for href in (
    "../research/robot-data.html",
    "cross-embodiment-learning.html",
    "robot-embodiment-benchmark.html",
):
    assert href in parser.links, f"Missing contextual internal link: {href}"

assert "cross-embodiment robotics data infrastructure" in listing.lower(), "Article listing summary is stale"
assert 'href="articles/cross-embodiment-robotics.html"' in listing, "Article listing link is missing"

root = ET.parse(SITEMAP_PATH).getroot()
ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
entry = next(
    (node for node in root.findall("sm:url", ns)
     if node.findtext("sm:loc", namespaces=ns) == PAGE_URL),
    None,
)
assert entry is not None, "Article is missing from sitemap"
assert entry.findtext("sm:lastmod", namespaces=ns) == EXPECTED_MODIFIED, "Sitemap lastmod is missing or stale"

print("PASS: cross-embodiment data collection content, metadata, Article schema, internal links and sitemap lastmod")
