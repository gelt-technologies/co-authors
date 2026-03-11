AGENTS: dict[str, str] = {
    "claude": "Claude <claude[bot]@users.noreply.github.com>",
    "codex": "Codex <codex[bot]@users.noreply.github.com>",
    "cursor": "Cursor <cursor[bot]@users.noreply.github.com>",
}


def get_trailer(agent_key: str) -> str | None:
    """Return the Co-Authored-By trailer for a given agent key, or None if unknown."""
    identity = AGENTS.get(agent_key.lower())
    return f"Co-Authored-By: {identity}" if identity else None
