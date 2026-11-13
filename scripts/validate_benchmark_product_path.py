#!/usr/bin/env python3
"""Regression checks for the related HumanoidBehavior benchmark referral."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "index.html").read_text(encoding="utf-8")
SITEMAP = ET.parse(ROOT / "sitemap.xml").getroot()
NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

SECTION = re.search(
    r'<section class="section signal-section" id="benchmark-workspace">(.*?)</section>',
    HTML,
    re.S,
)
assert SECTION, "The benchmark referral section must exist on the homepage."
body = SECTION.group(1)

assert "Related platform · same robotics portfolio" in body, "The relationship must be disclosed."
assert "Turn robot behavior ideas into measured experiments." in body
assert "controlled MuJoCo evaluations with explicit seeds and policy versions" in body
assert "Each run is stored with its configuration and results in a workspace." in body
assert "reproducible mujoco benchmarks" not in body.lower()
assert "Each run is stored with its configuration and results in a workspace." in body
assert "does not replace validation on the target robot" in body

link = re.search(
    r'<a class="btn primary" href="https://humanoidbehavior\.com/benchmark\.html" '
    r'rel="noopener noreferrer">Explore the benchmark workspace →</a>',
    body,
)
assert link, "The contextual CTA must point to the public benchmark workspace."
assert HTML.count('href="https://humanoidbehavior.com/benchmark.html"') == 1, (
    "The homepage must expose exactly one contextual benchmark CTA."
)
assert HTML.index("<main>") < SECTION.start() < HTML.index("</main>"), (
    "The referral must remain in the main page content."
)

homepage_entry = next(
    (url for url in SITEMAP.findall("sm:url", NS)
     if url.findtext("sm:loc", namespaces=NS) == "https://robotembodiment.com/"),
    None,
)
assert homepage_entry is not None, "Homepage must remain in the sitemap."
assert homepage_entry.findtext("sm:lastmod", namespaces=NS) == "2026-11-13", (
    "Homepage sitemap lastmod must match the new homepage content."
)

print("PASS: related-product disclosure, benchmark claims, CTA destination, placement and sitemap lastmod")
