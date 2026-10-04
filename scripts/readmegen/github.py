"""Fetch a user's public GitHub numbers in one paginated GraphQL query."""

from __future__ import annotations

import json
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime

QUERY = """
query($login: String!, $after: String) {
  user(login: $login) {
    login name websiteUrl createdAt
    followers { totalCount }
    pinnedItems(first: 6, types: REPOSITORY) { nodes { ... on Repository { ...repo } } }
    contributionsCollection {
      totalCommitContributions totalPullRequestContributions totalIssueContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount contributionLevel } }
      }
    }
    repositories(first: 100, after: $after, ownerAffiliations: OWNER, privacy: PUBLIC,
                 isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        ...repo
        pushedAt
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name color } }
        }
      }
    }
  }
}
fragment repo on Repository {
  name description url stargazerCount primaryLanguage { name color }
}
"""

LEVELS = {"NONE": 0, "FIRST_QUARTILE": 1, "SECOND_QUARTILE": 2, "THIRD_QUARTILE": 3,
          "FOURTH_QUARTILE": 4}  # fmt: skip


@dataclass(frozen=True)
class Repo:
    name: str
    description: str | None
    url: str
    stars: int
    language: str | None
    pushed_at: datetime | None = None


@dataclass(frozen=True)
class Day:
    date: date
    count: int
    level: int  # 0 (none) .. 4, GitHub's own quartiles


@dataclass(frozen=True)
class Language:
    name: str
    share: float
    color: str


@dataclass(frozen=True)
class Stats:
    login: str
    name: str | None
    website: str | None
    created_at: datetime
    followers: int
    repos: int
    stars: int
    commits: int
    pull_requests: int
    issues: int
    contributions: int
    languages: list[Language]
    days: list[Day]
    pinned: list[Repo]
    recent: list[Repo]  # most recently pushed first

    def featured(self, limit: int = 4) -> list[Repo]:
        """Pinned repos, or the most-starred ones when nothing is pinned."""
        if self.pinned:
            return self.pinned[:limit]
        return sorted(self.recent, key=lambda repo: -repo.stars)[:limit]

    def streaks(self) -> tuple[int, int]:
        """(current, longest) run of days with contributions. A quiet today keeps the streak."""
        longest = run = 0
        for day in self.days:
            run = run + 1 if day.count else 0
            longest = max(longest, run)
        days = self.days[:-1] if self.days and not self.days[-1].count else self.days
        current = 0
        for day in reversed(days):
            if not day.count:
                break
            current += 1
        return current, longest

    @property
    def active_days(self) -> int:
        return sum(1 for day in self.days if day.count)


def fetch_pages(login: str, token: str) -> list[dict]:
    """Raw `user` payloads, one per page of repositories."""
    pages, after = [], None
    while True:
        data = _graphql({"login": login, "after": after}, token)
        if data.get("user") is None:
            raise RuntimeError(f"GitHub user {login!r} not found")
        pages.append(data["user"])
        info = data["user"]["repositories"]["pageInfo"]
        if not info["hasNextPage"]:
            return pages
        after = info["endCursor"]


def _graphql(variables: dict, token: str) -> dict:
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": variables}).encode(),
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-readme-builder",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if payload.get("errors"):
        raise RuntimeError(f"GitHub GraphQL error: {payload['errors']}")
    return payload["data"]


def summarize(pages: list[dict]) -> Stats:
    """Fold the paginated payloads from QUERY into Stats."""
    user = pages[0]
    nodes = [repo for page in pages for repo in page["repositories"]["nodes"]]
    sizes: Counter[str] = Counter()
    colors: dict[str, str] = {}
    for repo in nodes:
        for edge in repo["languages"]["edges"]:
            sizes[edge["node"]["name"]] += edge["size"]
            colors[edge["node"]["name"]] = edge["node"]["color"] or "#8b949e"
    total = sum(sizes.values())
    contributions = user["contributionsCollection"]
    calendar = contributions["contributionCalendar"]
    return Stats(
        login=user["login"],
        name=user["name"] or None,
        website=user["websiteUrl"] or None,
        created_at=_datetime(user["createdAt"]),
        followers=user["followers"]["totalCount"],
        repos=user["repositories"]["totalCount"],
        stars=sum(repo["stargazerCount"] for repo in nodes),
        commits=contributions["totalCommitContributions"],
        pull_requests=contributions["totalPullRequestContributions"],
        issues=contributions["totalIssueContributions"],
        contributions=calendar["totalContributions"],
        languages=[Language(n, s / total, colors[n]) for n, s in sizes.most_common()]
        if total
        else [],
        days=[
            Day(
                date.fromisoformat(d["date"]),
                d["contributionCount"],
                LEVELS[d["contributionLevel"]],
            )
            for week in calendar["weeks"]
            for d in week["contributionDays"]
        ],
        pinned=[_repo(node) for node in user["pinnedItems"]["nodes"] if node],
        recent=[_repo(node) for node in nodes],
    )


def _repo(node: dict) -> Repo:
    language = node.get("primaryLanguage") or {}
    pushed = node.get("pushedAt")
    return Repo(
        name=node["name"],
        description=node["description"] or None,
        url=node["url"],
        stars=node["stargazerCount"],
        language=language.get("name"),
        pushed_at=_datetime(pushed) if pushed else None,
    )


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def uptime(since: datetime, now: datetime) -> tuple[int, int]:
    """Whole (years, months) between two instants."""
    months = (now.year - since.year) * 12 + (now.month - since.month)
    if (now.day, now.time()) < (since.day, since.time()):
        months -= 1
    return divmod(max(months, 0), 12)
