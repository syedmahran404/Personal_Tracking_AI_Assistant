"""Application classification — maps app names/bundles to productivity classes.

Strategy: a curated keyword map for common apps. Unknown apps default to
NEUTRAL but can be overridden per-user later (future: user_overrides table).
This is fast, deterministic, and auditable — preferred over an LLM call.
"""
from __future__ import annotations

from app.models.app_usage import ProductivityClass

# Lower-cased substrings → category. Order matters: first match wins.
_RULES: tuple[tuple[str, ProductivityClass], ...] = (
    # ─── Productive: code + docs + work tools ─────────────
    ("code", ProductivityClass.PRODUCTIVE),
    ("vscode", ProductivityClass.PRODUCTIVE),
    ("visual studio", ProductivityClass.PRODUCTIVE),
    ("intellij", ProductivityClass.PRODUCTIVE),
    ("pycharm", ProductivityClass.PRODUCTIVE),
    ("webstorm", ProductivityClass.PRODUCTIVE),
    ("rider", ProductivityClass.PRODUCTIVE),
    ("goland", ProductivityClass.PRODUCTIVE),
    ("clion", ProductivityClass.PRODUCTIVE),
    ("xcode", ProductivityClass.PRODUCTIVE),
    ("android studio", ProductivityClass.PRODUCTIVE),
    ("sublime", ProductivityClass.PRODUCTIVE),
    ("neovim", ProductivityClass.PRODUCTIVE),
    ("vim", ProductivityClass.PRODUCTIVE),
    ("emacs", ProductivityClass.PRODUCTIVE),
    ("zed", ProductivityClass.PRODUCTIVE),
    ("cursor", ProductivityClass.PRODUCTIVE),
    ("terminal", ProductivityClass.PRODUCTIVE),
    ("iterm", ProductivityClass.PRODUCTIVE),
    ("warp", ProductivityClass.PRODUCTIVE),
    ("alacritty", ProductivityClass.PRODUCTIVE),
    ("powershell", ProductivityClass.PRODUCTIVE),
    ("windowsterminal", ProductivityClass.PRODUCTIVE),
    ("notion", ProductivityClass.PRODUCTIVE),
    ("obsidian", ProductivityClass.PRODUCTIVE),
    ("logseq", ProductivityClass.PRODUCTIVE),
    ("figma", ProductivityClass.PRODUCTIVE),
    ("postman", ProductivityClass.PRODUCTIVE),
    ("insomnia", ProductivityClass.PRODUCTIVE),
    ("docker", ProductivityClass.PRODUCTIVE),
    ("dbeaver", ProductivityClass.PRODUCTIVE),
    ("tableplus", ProductivityClass.PRODUCTIVE),
    ("excel", ProductivityClass.PRODUCTIVE),
    ("word", ProductivityClass.PRODUCTIVE),
    ("powerpoint", ProductivityClass.PRODUCTIVE),
    ("google docs", ProductivityClass.PRODUCTIVE),
    ("sheets", ProductivityClass.PRODUCTIVE),
    ("linear", ProductivityClass.PRODUCTIVE),
    ("jira", ProductivityClass.PRODUCTIVE),
    ("github", ProductivityClass.PRODUCTIVE),
    ("gitlab", ProductivityClass.PRODUCTIVE),

    # ─── Distracting: social + entertainment + games ──────
    ("youtube", ProductivityClass.DISTRACTING),
    ("netflix", ProductivityClass.DISTRACTING),
    ("twitch", ProductivityClass.DISTRACTING),
    ("tiktok", ProductivityClass.DISTRACTING),
    ("instagram", ProductivityClass.DISTRACTING),
    ("facebook", ProductivityClass.DISTRACTING),
    ("twitter", ProductivityClass.DISTRACTING),
    ("x.com", ProductivityClass.DISTRACTING),
    ("reddit", ProductivityClass.DISTRACTING),
    ("discord", ProductivityClass.DISTRACTING),
    ("steam", ProductivityClass.DISTRACTING),
    ("spotify", ProductivityClass.DISTRACTING),  # debatable; default to distracting
    ("epic games", ProductivityClass.DISTRACTING),
    ("league of legends", ProductivityClass.DISTRACTING),
    ("valorant", ProductivityClass.DISTRACTING),
    ("minecraft", ProductivityClass.DISTRACTING),
    ("whatsapp", ProductivityClass.DISTRACTING),
    ("telegram", ProductivityClass.DISTRACTING),

    # ─── Neutral: browsers, file managers, system ─────────
    ("chrome", ProductivityClass.NEUTRAL),
    ("firefox", ProductivityClass.NEUTRAL),
    ("safari", ProductivityClass.NEUTRAL),
    ("edge", ProductivityClass.NEUTRAL),
    ("brave", ProductivityClass.NEUTRAL),
    ("arc", ProductivityClass.NEUTRAL),
    ("finder", ProductivityClass.NEUTRAL),
    ("explorer", ProductivityClass.NEUTRAL),
    ("slack", ProductivityClass.NEUTRAL),
    ("teams", ProductivityClass.NEUTRAL),
    ("zoom", ProductivityClass.NEUTRAL),
    ("mail", ProductivityClass.NEUTRAL),
    ("outlook", ProductivityClass.NEUTRAL),
)


def classify_app(app_name: str | None, window_title: str | None = None) -> ProductivityClass:
    """Classify an app/window into a productivity class.

    The window title is also inspected — e.g. Chrome on YouTube becomes
    distracting, Chrome on GitHub becomes productive.
    """
    haystack = " ".join(filter(None, [app_name, window_title])).lower()
    if not haystack:
        return ProductivityClass.UNKNOWN
    for needle, cls in _RULES:
        if needle in haystack:
            return cls
    return ProductivityClass.NEUTRAL
