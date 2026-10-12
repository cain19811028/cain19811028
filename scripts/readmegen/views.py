"""Profile views: read komarev's live counter and draw the count as a local badge.

komarev answers with no-store (every load is a view), so GitHub's camo proxy has
to fetch it live on each profile visit, and any slow or failed fetch shows up as
a broken image. The README therefore loads komarev only as an invisible 1px pixel
that does the counting, and shows this badge, served from the repo, instead.
"""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from .svg import LIGHT, escape, num

COUNTER = "https://komarev.com/ghpvc/"
_SVG = "{http://www.w3.org/2000/svg}"
_COUNT = re.compile(r"\d{1,3}(,\d{3})*")  # komarev groups thousands with commas

# Drawn like the shields.io flat-square badges next to it: Verdana 11px, 5px padding.
LABEL = "profile views"
LABEL_WIDTH = 69  # shields' measure of LABEL
DIGIT, COMMA = 1302 / 2048 * 11, 745 / 2048 * 11  # Verdana advance widths at 11px
PADDING = 5


def fetch_count(login: str) -> int:
    """The live count. komarev only counts requests from GitHub's camo, so this adds no view."""
    url = f"{COUNTER}?{urllib.parse.urlencode({'username': login})}"
    request = urllib.request.Request(url, headers={"User-Agent": "profile-readme-builder"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return parse_count(response.read().decode("utf-8"))


def parse_count(badge_svg: str) -> int:
    """The number on komarev's badge; ValueError when it shows anything else, e.g. an error."""
    try:
        root = ET.fromstring(badge_svg)
    except ET.ParseError as error:
        raise ValueError(f"counter did not answer with SVG: {error}") from error
    texts = [(text.text or "").strip() for text in root.iter(f"{_SVG}text")]
    if not texts or not _COUNT.fullmatch(texts[-1]):
        raise ValueError(f"counter badge shows no count: {texts!r}")
    return int(texts[-1].replace(",", ""))


def _text_width(text: str) -> int:
    """shields' rule: truncate, then round up to odd so the text centres on whole pixels."""
    width = int(sum(COMMA if ch == "," else DIGIT for ch in text))
    return width if width % 2 else width + 1


def badge(count: int) -> str:
    message = f"{count:,}"
    message_width = _text_width(message)
    left = LABEL_WIDTH + 2 * PADDING
    right = message_width + 2 * PADDING
    label = escape(f"{LABEL}: {message}")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{left + right}" height="20" '
        f'role="img" aria-label="{label}"><title>{label}</title>'
        f'<g shape-rendering="crispEdges"><rect width="{left}" height="20" fill="#555"/>'
        f'<rect x="{left}" width="{right}" height="20" fill="{LIGHT["accent"]}"/></g>'
        '<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" '
        'text-rendering="geometricPrecision" font-size="11">'
        f'<text x="{num(1 + LABEL_WIDTH / 2 + PADDING)}" y="14" '
        f'textLength="{LABEL_WIDTH}">{LABEL}</text>'
        f'<text x="{num(left - 1 + message_width / 2 + PADDING)}" y="14" '
        f'textLength="{message_width}">{message}</text>'
        "</g></svg>\n"
    )
