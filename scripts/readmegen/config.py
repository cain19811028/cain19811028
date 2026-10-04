"""Everything personal on the profile page. Edit freely; the workflow picks it up."""

LOGIN = "cain19811028"

# Hero card ("Claude Code welcome screen").
GREETING = "Welcome back, Cain!"
DISPLAY_NAME = "Hung-Chun Chen · 諶宏軍"
WORKDIR = "~/github/cain19811028"
CURRENTLY = [
    ("learning", "Go · Python · cloud notes"),
    ("pairing with", "Claude Code"),
    ("writing at", "cain19811028.blogspot.tw"),
]
# Typed one after another in the hero's prompt box. {years} = whole years on GitHub.
PROMPTS = [
    "summarize my {years} years on GitHub",
    "keep the Go & Python notebooks growing",
    "regenerate this profile every 6 hours",
    "say hi to whoever is reading this",
]

# Repos never shown in "Recent activity" (the bot commits to this one all the time).
HIDDEN_REPOS = {LOGIN}
