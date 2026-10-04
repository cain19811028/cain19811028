"""Shared SVG pieces: theme colours, card chrome, glyph-exact text and Clawd.

GitHub shows README images through <img>, so every file must be self-contained:
no scripts, no external fonts or images. Motion is plain CSS and stops under
prefers-reduced-motion. Colours follow the viewer's light/dark preference.
"""

from __future__ import annotations

import unicodedata
from xml.sax.saxutils import escape as _escape

FONT = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"

LIGHT = {
    "bg": "#faf9f5", "border": "#e8e6dc", "fg": "#141413", "text": "#3d3929",
    "muted": "#87867f", "accent": "#d97757", "num": "#2f6fd6", "track": "#ece9e0",
    "clawd": "#dd876c", "ink": "#141413",
    "l0": "#efede6", "l1": "#f6d8c9", "l2": "#efb497", "l3": "#e5916f", "l4": "#d97757",
}  # fmt: skip
DARK = {
    "bg": "#1f1e1d", "border": "#3d3d3a", "fg": "#faf9f5", "text": "#e8e6dc",
    "muted": "#9c9a92", "accent": "#d97757", "num": "#8ab4f8", "track": "#33322f",
    "clawd": "#dd876c", "ink": "#000000",
    "l0": "#2b2a28", "l1": "#4d3026", "l2": "#7a4430", "l3": "#ad5a3b", "l4": "#e07b55",
}  # fmt: skip


def escape(text: str) -> str:
    return _escape(text, {'"': "&quot;"})


def num(value: float) -> str:
    return f"{value:.2f}".rstrip("0").rstrip(".")


def theme_css() -> str:
    def block(colors: dict[str, str]) -> str:
        return "svg{" + "".join(f"--{k}:{v};" for k, v in colors.items()) + "}"

    return (
        block(LIGHT)
        + "@media (prefers-color-scheme:dark){"
        + block(DARK)
        + "}"
        + f"text{{font-family:{FONT};fill:var(--text);white-space:pre}}"
        + ".fg{fill:var(--fg)}.mu{fill:var(--muted)}.ac{fill:var(--accent)}.nm{fill:var(--num)}"
        + ".b{font-weight:700}"
    )


REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def document(width: float, height: float, label: str, css: str, body: list[str]) -> str:
    w, h = num(width), num(height)
    head = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(label)}">'
    )
    style = f"<style>{theme_css()}{css}{REDUCED_MOTION}</style>"
    return "\n".join([head, style, *body, "</svg>"]) + "\n"


def window(width: float, height: float, title: str) -> list[str]:
    """A small editor window: rounded card, three dots, file name."""
    return [
        f'<rect x=".5" y=".5" width="{num(width - 1)}" height="{num(height - 1)}" rx="10" '
        'style="fill:var(--bg);stroke:var(--border)"/>',
        *(
            f'<circle cx="{18 + i * 14}" cy="18" r="4" style="fill:var(--{c})"/>'
            for i, c in enumerate(["accent", "muted", "border"])
        ),
        f'<text class="mu" x="64" y="22" font-size="12">{escape(title)}</text>',
        f'<line x1="1" y1="34" x2="{num(width - 1)}" y2="34" style="stroke:var(--border)"/>',
    ]


def display_width(text: str) -> int:
    """Terminal columns: East Asian wide characters take two."""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def mono(text: str, x: float, y: float, size: float, cls: str = "", style: str = "") -> str:
    """Text with every glyph placed on a fixed grid, so overlays line up in any font."""
    advance, xs, col = size * 0.6, [], 0
    for ch in text:
        xs.append(num(x + col * advance))
        col += display_width(ch)
    xs = " ".join(xs)
    cls_attr = f' class="{cls}"' if cls else ""
    style_attr = f' style="{style}"' if style else ""
    return (
        f'<text{cls_attr} x="{xs}" y="{num(y)}" font-size="{num(size)}"{style_attr}>'
        f"{escape(text)}</text>"
    )


# --- Clawd ------------------------------------------------------------------------------
# Measured from Anthropic's clawd.gif, in its own pixels; (0, 0) is the body's top-left.
CLAWD_BOX = (-14, 0, 102, 66)  # x, y, width, height
_BODY = [(0, 0, 74, 46), (-14, 20, 14, 13), (74, 20, 14, 13)]
_EYES = [(13, 13, 7, 13), (54, 13, 7, 13)]
_LEGS = [(7, 46, 7, 14), (20, 46, 7, 14), (47, 46, 7, 14), (60, 46, 7, 14)]
_SHADOW = (7, 60, 60, 6)

CLAWD_CSS = (
    ".cl-body{animation:cl-bob 1.6s ease-in-out infinite}"
    "@keyframes cl-bob{0%,100%{transform:translateY(0)}50%{transform:translateY(4px)}}"
    ".cl-legs{transform-box:fill-box;transform-origin:50% 100%;"
    "animation:cl-legs 1.6s ease-in-out infinite}"
    "@keyframes cl-legs{0%,100%{transform:scaleY(1)}50%{transform:scaleY(.715)}}"
    ".cl-eyes{transform-box:fill-box;transform-origin:center;animation:cl-blink 3.2s infinite}"
    "@keyframes cl-blink{0%,80%,90%,100%{transform:scaleY(1)}85%{transform:scaleY(.1)}}"
)


def clawd(x: float, y: float, scale: float) -> str:
    """Clawd with its top-left bounding-box corner at (x, y)."""

    def rects(boxes, style: str) -> str:
        return "".join(
            f'<rect x="{bx}" y="{by}" width="{w}" height="{h}" style="{style}"/>'
            for bx, by, w, h in boxes
        )

    ox, oy = x - CLAWD_BOX[0] * scale, y - CLAWD_BOX[1] * scale
    return (
        f'<g transform="translate({num(ox)} {num(oy)}) scale({num(scale)})" '
        'shape-rendering="crispEdges">'
        + rects([_SHADOW], "fill:var(--ink)")
        + f'<g class="cl-legs">{rects(_LEGS, "fill:var(--clawd)")}</g>'
        + '<g class="cl-body">'
        + rects(_BODY, "fill:var(--clawd)")
        + f'<g class="cl-eyes">{rects(_EYES, "fill:var(--ink)")}</g>'
        + "</g></g>"
    )
