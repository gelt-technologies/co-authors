AGENTS: dict[str, str] = {
    "claude": "Claude <noreply@anthropic.com>",
    "codex": "Codex <codex@openai.com>",
    "cursor": "Cursor <cursoragent@cursor.com>",
}


def get_trailer(agent_key: str) -> str | None:
    """Return the Co-Authored-By trailer for a given agent key, or None if unknown."""
    identity = AGENTS.get(agent_key.lower())
    return f"Co-Authored-By: {identity}" if identity else None
