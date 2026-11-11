#!/usr/bin/env python3
"""Keep the Robot Embodiment homepage free of unrelated floating cross-brand promotions."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HOME = (ROOT / "index.html").read_text(encoding="utf-8")

assert "Domainzax" not in HOME, "Homepage must not display unrelated Domainzax branding"
assert "discord.gg/ewUr2dmt" not in HOME, "Homepage must not link to the unrelated Domainzax Discord"
floating_external_ctas = re.findall(
    r'<a\b(?=[^>]*href="https?://)(?=[^>]*style="[^"]*position\s*:\s*fixed)[^>]*>',
    HOME,
    re.I,
)
assert not floating_external_ctas, "Homepage must not contain a fixed-position external promotional overlay"

print("PASS: homepage contains no unrelated Domainzax branding or fixed external promotional overlay")
