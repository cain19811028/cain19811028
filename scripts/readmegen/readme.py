"""Keep the generated part of README.md (between markers) up to date."""

from __future__ import annotations

from .github import Repo

START, END = "<!-- projects:start -->", "<!-- projects:end -->"


def projects_table(repos: list[Repo]) -> str:
    lines = ["| Project | About | Language | ★ |", "| --- | --- | --- | ---: |"]
    for repo in repos:
        lines.append(
            f"| [**{_cell(repo.name)}**]({repo.url}) | {_cell(repo.description or '—')} "
            f"| {_cell(repo.language or '—')} | {repo.stars} |"
        )
    return "\n".join(lines)


def _cell(text: str) -> str:
    """Keep table rows intact: no pipes or line breaks inside a cell."""
    return " ".join(text.split()).replace("|", "\\|")


def replace_block(readme: str, content: str) -> str:
    start, end = readme.find(START), readme.find(END)
    if start < 0 or end < start:
        raise ValueError(f"README.md needs {START} and {END} around the generated table")
    return readme[: start + len(START)] + "\n" + content + "\n" + readme[end:]
