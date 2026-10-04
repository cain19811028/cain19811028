"""Fake GraphQL payloads shaped like readmegen.github.QUERY results."""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]


def repo(name, stars=0, language="Python", pushed="2026-10-01T00:00:00Z", langs=(), desc=None):
    return {
        "name": name,
        "description": desc,
        "url": f"https://github.com/u/{name}",
        "stargazerCount": stars,
        "primaryLanguage": {"name": language, "color": "#3572A5"} if language else None,
        "pushedAt": pushed,
        "languages": {
            "edges": [{"size": s, "node": {"name": n, "color": c}} for n, s, c in langs]
        },
    }


def page(repos=(), pinned=(), counts=(), last_day=date(2026, 10, 4), total_repos=None):
    first = last_day - timedelta(days=len(counts) - 1)
    days = [
        {
            "date": (first + timedelta(days=i)).isoformat(),
            "contributionCount": n,
            "contributionLevel": LEVELS[min(n, 4)],
        }
        for i, n in enumerate(counts)
    ]
    return {
        "login": "u",
        "name": "",
        "websiteUrl": None,
        "createdAt": "2012-03-07T13:17:34Z",
        "followers": {"totalCount": 5},
        "pinnedItems": {"nodes": list(pinned)},
        "contributionsCollection": {
            "totalCommitContributions": 7,
            "totalPullRequestContributions": 2,
            "totalIssueContributions": 1,
            "contributionCalendar": {
                "totalContributions": sum(counts),
                "weeks": [{"contributionDays": days[i : i + 7]} for i in range(0, len(days), 7)],
            },
        },
        "repositories": {
            "totalCount": len(repos) if total_repos is None else total_repos,
            "pageInfo": {"hasNextPage": False, "endCursor": None},
            "nodes": list(repos),
        },
    }
