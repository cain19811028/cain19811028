"""The four generated images: hero, stats, languages and contribution activity."""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from . import config
from .github import Stats, uptime
from .svg import CLAWD_BOX, CLAWD_CSS, clawd, display_width, document, mono, num, window

FADE_CSS = ".fade{animation:fade .5s ease-out backwards}@keyframes fade{from{opacity:0}}"


def _delay(seconds: float) -> str:
    return f"animation-delay:{num(seconds)}s"


# --- hero ---------------------------------------------------------------------------------
HERO_W, HERO_H = 840, 340
PROMPT_SIZE = 13
TYPE_SECONDS, HOLD_SECONDS, ERASE_SECONDS, GAP_SECONDS = 0.055, 1.8, 0.025, 0.35


def typing_schedule(lengths: list[int]) -> tuple[float, list[tuple[float, float, float, float]]]:
    """Per prompt: (start, typed, erase_start, end) seconds within one loop of `total`."""
    t, slots = 0.0, []
    for n in lengths:
        typed = t + n * TYPE_SECONDS
        erase = typed + HOLD_SECONDS
        end = erase + n * ERASE_SECONDS + GAP_SECONDS
        slots.append((t, typed, erase, end))
        t = end
    return t, slots


def _typing(prompts: list[str], x: float, y: float) -> tuple[str, list[str]]:
    """Prompts typed one after another: a caret drags a cover that hides the untyped text."""
    advance = PROMPT_SIZE * 0.6
    total, slots = typing_schedule([len(p) for p in prompts])

    def pct(seconds: float) -> str:
        return num(100 * seconds / total) + "%"

    css, body = [], []
    move = ["0%{transform:translateX(0)}"]
    for i, (prompt, (start, typed, erase, end)) in enumerate(zip(prompts, slots)):
        width = num(len(prompt) * advance)
        steps = f"animation-timing-function:steps({len(prompt)},end)"
        move.append(f"{pct(start)}{{transform:translateX(0);{steps}}}")
        move.append(f"{pct(typed)}{{transform:translateX({width}px)}}")
        move.append(f"{pct(erase)}{{transform:translateX({width}px);{steps}}}")
        move.append(f"{pct(erase + len(prompt) * ERASE_SECONDS)}{{transform:translateX(0)}}")
        shown = f"{pct(start)}{{opacity:1}}{pct(end)}{{opacity:0}}"
        css.append(
            f"@keyframes pr{i}{{0%{{opacity:{int(i == 0)}}}{shown}}}"
            f".pr{i}{{opacity:{int(i == 0)};animation:pr{i} {num(total)}s step-end infinite}}"
        )
        body.append(mono(prompt, x, y, PROMPT_SIZE, f"fg pr{i}"))
    move.append("100%{transform:translateX(0)}")
    first = num(len(prompts[0]) * advance)
    css.append(
        f"@keyframes caret{{{''.join(move)}}}"
        f".caret{{transform:translateX({first}px);animation:caret {num(total)}s infinite}}"
        ".blink{animation:blink 1s step-end infinite}@keyframes blink{50%{opacity:0}}"
    )
    longest = max(len(p) for p in prompts) * advance
    body.append(
        f'<g class="caret"><rect x="{num(x)}" y="{num(y - 14)}" width="{num(longest + 20)}" '
        'height="20" style="fill:var(--bg)"/>'
        f'<rect class="blink" x="{num(x)}" y="{num(y - 12)}" width="{num(advance)}" '
        'height="16" style="fill:var(--accent)"/></g>'
    )
    return "".join(css), body


def hero(stats: Stats, now: datetime) -> str:
    years, months = uptime(stats.created_at, now)
    prompts = [p.format(years=years) for p in config.PROMPTS]
    body = [
        f'<rect x=".5" y=".5" width="{HERO_W - 1}" height="{HERO_H - 1}" rx="12" '
        'style="fill:var(--bg);stroke:var(--border)"/>',
        '<rect x="20" y="24" width="800" height="220" rx="10" '
        'style="fill:none;stroke:var(--accent);stroke-width:1.4"/>',
    ]
    title = f" ✻ {stats.login} v{years}.{months} "
    body.append(
        f'<rect x="34" y="16" width="{num(display_width(title) * 7.8)}" height="16" '
        'style="fill:var(--bg)"/>'
    )
    body.append(mono(title, 34, 29, 13, "ac b"))

    # Left column: greeting, Clawd, who and where.
    cx = 205

    def centred(text: str, y: float, size: float, cls: str) -> str:
        return mono(text, cx - display_width(text) * size * 0.6 / 2, y, size, cls)

    scale = 1.3
    body.append(centred(config.GREETING, 66, 15, "fg b"))
    body.append(clawd(cx - CLAWD_BOX[2] * scale / 2, 84, scale))
    body.append(centred(config.DISPLAY_NAME, 196, 13, "mu"))
    body.append(centred(config.WORKDIR, 217, 12, "mu"))
    body.append(
        '<line x1="400" y1="42" x2="400" y2="226" style="stroke:var(--accent);opacity:.35"/>'
    )

    # Right column: what happened lately, what's going on.
    x = 424
    body.append(mono("Recent activity", x, 62, 13, "ac b"))
    recent = [r for r in stats.recent if r.name not in config.HIDDEN_REPOS][:3]
    for i, repo in enumerate(recent):
        y = 86 + i * 20
        name = repo.name if len(repo.name) <= 27 else repo.name[:26] + "…"
        body.append(mono(name, x, y, 12, "fg"))
        if repo.pushed_at:
            body.append(mono(f"pushed {repo.pushed_at:%Y-%m-%d}", x + 28 * 7.2, y, 12, "mu"))
    body.append(mono("Currently", x, 164, 13, "ac b"))
    for i, (key, value) in enumerate(config.CURRENTLY):
        y = 188 + i * 20
        body.append(mono(key, x, y, 12, "mu"))
        body.append(mono(value, x + 14 * 7.2, y, 12, "fg"))

    # Prompt box with the typing animation, plus the footer hints.
    body.append(
        '<rect x="20" y="258" width="800" height="40" rx="8" '
        'style="fill:var(--bg);stroke:var(--muted);stroke-opacity:.6"/>'
    )
    body.append(mono(">", 36, 283, PROMPT_SIZE, "fg b"))
    typing_css, typing_body = _typing(prompts, 54, 283)
    body += typing_body
    body.append(mono("? for shortcuts", 26, 322, 11, "mu"))
    note = "regenerated every 6h by GitHub Actions"
    body.append(mono(note, 814 - len(note) * 6.6, 322, 11, "mu"))

    label = f"{stats.login}: Clawd waving from a Claude Code welcome screen"
    return document(HERO_W, HERO_H, label, CLAWD_CSS + typing_css, body)


# --- stats ----------------------------------------------------------------------------------
CARD_W, CARD_H = 410, 236


def stats_card(stats: Stats) -> str:
    entries = [
        ("stars", stats.stars),
        ("repos", stats.repos),
        ("followers", stats.followers),
        ("contributions_1y", stats.contributions),
        ("commits_1y", stats.commits),
        ("pull_requests_1y", stats.pull_requests),
        ("issues_1y", stats.issues),
    ]
    body = window(CARD_W, CARD_H, "stats.json")
    lines = [[("{", "mu")]]
    for i, (key, value) in enumerate(entries):
        comma = "," if i < len(entries) - 1 else ""
        quoted = f'"{key}"'
        lines.append(
            [("  " + quoted, "ac"), (":" + " " * (19 - len(quoted)), "mu"), (str(value), "nm"),
             (comma, "mu")]
        )  # fmt: skip
    lines.append([("}", "mu")])
    for row, parts in enumerate(lines):
        y, col = 60 + row * 19, 0
        for text, cls in parts:
            body.append(mono(text, 24 + col * 7.8, y, 13, f"{cls} fade", _delay(0.1 + row * 0.06)))
            col += len(text)

    days = len(stats.days) or 1
    share = stats.active_days / days
    r, cx, cy = 46, 330, 132
    circumference = 2 * math.pi * r
    offset = circumference * (1 - share)
    body += [
        f'<circle cx="{cx}" cy="{cy}" r="{r}" style="fill:none;stroke:var(--track);'
        'stroke-width:9"/>',
        f'<circle class="ring" cx="{cx}" cy="{cy}" r="{r}" transform="rotate(-90 {cx} {cy})" '
        f'style="fill:none;stroke:var(--accent);stroke-width:9;stroke-linecap:round;'
        f'stroke-dasharray:{num(circumference)};stroke-dashoffset:{num(offset)}"/>',
        mono(str(stats.active_days), cx - len(str(stats.active_days)) * 6.6, cy + 4, 22, "fg b"),
        mono(f"/ {days} days", cx - len(f"/ {days} days") * 3, cy + 22, 10, "mu"),
        mono("active days", cx - 11 * 3.6, cy + r + 30, 12, "mu"),
    ]
    css = (
        FADE_CSS + f".ring{{animation:ring 1.2s ease-out .3s backwards}}"
        f"@keyframes ring{{from{{stroke-dashoffset:{num(circumference)}}}}}"
    )
    label = (
        f"{stats.login} stats: {stats.stars} stars, {stats.repos} repos, "
        f"{stats.contributions} contributions and {stats.active_days} active days in the last year"
    )
    return document(CARD_W, CARD_H, label, css, body)


# --- languages ------------------------------------------------------------------------------
def languages_card(stats: Stats, limit: int = 8) -> str:
    shown = stats.languages[:limit]
    rest = 1 - sum(lang.share for lang in shown)
    rows = [(lang.name, lang.share, lang.color) for lang in shown]
    if rest > 0.0005:
        rows.append(("Other", rest, "#9c9a92"))
    body = window(CARD_W, CARD_H, "languages.yml")
    x0, width = 24, CARD_W - 48
    body.append(
        f'<clipPath id="bar"><rect x="{x0}" y="54" width="{width}" height="10" rx="5"/></clipPath>'
    )
    segments, x = [], float(x0)
    for name, share, color in rows:
        w = share * width
        segments.append(
            f'<rect x="{num(x)}" y="54" width="{num(w + 0.5)}" height="10" style="fill:{color}"/>'
        )
        x += w
    body.append(f'<g class="grow" clip-path="url(#bar)">{"".join(segments)}</g>')
    for i, (name, share, color) in enumerate(rows):
        col, row = divmod(i, (len(rows) + 1) // 2)
        lx, ly = x0 + col * 190, 96 + row * 24
        style = _delay(0.3 + i * 0.05)
        body.append(
            f'<circle class="fade" cx="{lx + 5}" cy="{ly - 4}" r="5" '
            f'style="fill:{color};{style}"/>'
        )
        label = name if len(name) <= 15 else name[:14] + "…"
        body.append(mono(label, lx + 16, ly, 12, "fg fade", style))
        pct = f"{share:.1%}"
        body.append(mono(pct, lx + 168 - len(pct) * 7.2, ly, 12, "mu fade", style))
    body.append(mono(f"# by bytes across {stats.repos} public repos", x0, CARD_H - 18, 11, "mu"))
    css = (
        FADE_CSS + ".grow{transform-box:fill-box;transform-origin:left;"
        "animation:grow .9s ease-out .15s backwards}@keyframes grow{from{transform:scaleX(0)}}"
    )
    top = ", ".join(f"{lang.name} {lang.share:.0%}" for lang in shown[:3])
    return document(CARD_W, CARD_H, f"{stats.login} top languages: {top}", css, body)


# --- activity ---------------------------------------------------------------------------------
ACT_W, ACT_H = 840, 214
CELL, STEP = 11, 14


def activity_card(stats: Stats) -> str:
    body = window(ACT_W, ACT_H, "contributions.log")
    x0, y0 = 56, 68
    if stats.days:
        first = stats.days[0].date
        sunday = first - timedelta(days=(first.weekday() + 1) % 7)
        weeks: dict[int, list[str]] = {}
        last_month, last_label_col = None, -9
        for day in stats.days:
            col = (day.date - sunday).days // 7
            row = (day.date.weekday() + 1) % 7
            weeks.setdefault(col, []).append(
                f'<rect x="{x0 + col * STEP}" y="{y0 + row * STEP}" width="{CELL}" '
                f'height="{CELL}" rx="2" style="fill:var(--l{day.level})"/>'
            )
            if day.date.month != last_month and col - last_label_col >= 3:
                body.append(mono(f"{day.date:%b}", x0 + col * STEP, 58, 10, "mu"))
                last_month, last_label_col = day.date.month, col
            last_month = day.date.month
        for col, cells in sorted(weeks.items()):
            body.append(f'<g class="pop" style="{_delay(0.1 + col * 0.012)}">{"".join(cells)}</g>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        body.append(mono(name, 24, y0 + row * STEP + 9, 10, "mu"))

    current, longest = stats.streaks()
    parts = [
        (f"{stats.contributions:,}", "ac b"), (" contributions in the last year  ·  ", "mu"),
        ("current streak ", "mu"), (f"{current}d", "ac b"), ("  ·  longest streak ", "mu"),
        (f"{longest}d", "ac b"),
    ]  # fmt: skip
    col = 0
    for text, cls in parts:
        body.append(mono(text, 24 + col * 7.2, 196, 12, cls))
        col += len(text)
    lx = ACT_W - 24 - 5 * STEP - 30
    body.append(mono("less", lx - 34, 196, 10, "mu"))
    for level in range(5):
        body.append(
            f'<rect x="{lx + level * STEP}" y="187" width="{CELL}" height="{CELL}" rx="2" '
            f'style="fill:var(--l{level})"/>'
        )
    body.append(mono("more", lx + 5 * STEP + 4, 196, 10, "mu"))
    css = ".pop{animation:fade .4s ease-out backwards}@keyframes fade{from{opacity:0}}"
    label = (
        f"{stats.login}: {stats.contributions} contributions in the last year, "
        f"current streak {current} days, longest {longest} days"
    )
    return document(ACT_W, ACT_H, label, css, body)
