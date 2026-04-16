from co_authors.agents import AGENTS, get_trailer


def test_known_agents_present():
    assert "claude" in AGENTS
    assert "codex" in AGENTS
    assert "cursor" in AGENTS


def test_get_trailer_known_key():
    assert get_trailer("claude") == "Co-Authored-By: Claude <noreply@anthropic.com>"
    assert get_trailer("codex") == "Co-Authored-By: Codex <codex@openai.com>"
    assert get_trailer("cursor") == "Co-Authored-By: Cursor <cursoragent@cursor.com>"


def test_get_trailer_unknown_key():
    assert get_trailer("unknown") is None
    assert get_trailer("") is None


def test_get_trailer_case_insensitive():
    assert get_trailer("Claude") == get_trailer("claude")
    assert get_trailer("Codex") == get_trailer("codex")
    assert get_trailer("Cursor") == get_trailer("cursor")
