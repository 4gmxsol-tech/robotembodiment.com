#!/usr/bin/env python3
"""Regression tests for pausing unapproved RobotEmbodiment acquisition messaging."""
from datetime import date
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
HOME = (ROOT / "index.html").read_text(encoding="utf-8")
ARTICLES = (ROOT / "articles.html").read_text(encoding="utf-8")
FOR_SALE = (ROOT / "for-sale.html").read_text(encoding="utf-8")
HANDOFF = (ROOT / "buyer-handoff.html").read_text(encoding="utf-8")
SITE_JS = (ROOT / "assets" / "site.js").read_text(encoding="utf-8")
SITE_CSS = (ROOT / "assets" / "site.css").read_text(encoding="utf-8")
SITEMAP = ET.parse(ROOT / "sitemap.xml").getroot()

for label, page in (("homepage", HOME), ("article index", ARTICLES)):
    assert "for-sale.html" not in page, f"{label} still links to the sale page"
    assert "buyer-handoff.html" not in page, f"{label} still links to the handoff page"
assert "Premium domain + developed knowledge property" not in HOME
assert "Explore acquisition" not in HOME
assert "Technical handoff" not in HOME
assert "Research-led knowledge property" in HOME
assert 'href="research.html">Explore research' in HOME

for label, page in (("for-sale status", FOR_SALE), ("technical overview", HANDOFF)):
    assert re.search(r'<meta\s+name="robots"\s+content="noindex,nofollow"', page, re.I), f"{label} must be noindex,nofollow"
assert "not currently being offered for sale or acquisition" in FOR_SALE.lower()
assert "does not make an offer" in FOR_SALE.lower()
assert "not a sale, acquisition, or transfer offer" in HANDOFF.lower()
assert "No transfer of the domain, repository, content, infrastructure, or accounts is authorized" in HANDOFF

ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
urls = {
    item.findtext(f"{ns}loc"): item.findtext(f"{ns}lastmod")
    for item in SITEMAP.findall(f"{ns}url")
}
assert "https://robotembodiment.com/for-sale.html" not in urls
assert "https://robotembodiment.com/buyer-handoff.html" not in urls
homepage_lastmod = urls.get("https://robotembodiment.com/")
assert homepage_lastmod, "Homepage must retain a sitemap lastmod"
assert date.fromisoformat(homepage_lastmod) >= date(2026, 11, 9), (
    "Homepage lastmod must not predate the 9 November removal of unapproved acquisition messaging"
)

assert "path.endsWith('/for-sale.html')" in SITE_JS
assert "path.endsWith('/buyer-handoff.html')" in SITE_JS
assert 'a[href$="for-sale.html"]' in SITE_CSS
assert 'a[href$="buyer-handoff.html"]' in SITE_CSS
print("PASS: no public acquisition CTA; status pages noindex; sitemap excludes sale/handoff pages; homepage lastmod does not predate the authorization-state change")
