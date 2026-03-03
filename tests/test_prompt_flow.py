from co_authors import _has_message_flag, _resolve_trailers


class TestHasMessageFlag:
    def test_short_flag(self):
        assert _has_message_flag(("-m", "fix: something"))

    def test_long_flag(self):
        assert _has_message_flag(("--message", "fix: something"))

    def test_not_present(self):
        assert not _has_message_flag(("--amend",))

    def test_empty(self):
        assert not _has_message_flag(())


class TestResolveTrailersPromptFlow:
    def test_no_git_agent_no_message_calls_prompt(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        monkeypatch.setattr(
            "co_authors.select_agent",
            lambda: "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>",
        )
        result = _resolve_trailers(())
        assert result == ("--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")

    def test_no_git_agent_no_message_prompt_returns_none(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        monkeypatch.setattr("co_authors.select_agent", lambda: None)
        result = _resolve_trailers(())
        assert result is None

    def test_no_git_agent_with_message_skips_prompt(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        called = []
        monkeypatch.setattr(
            "co_authors.select_agent", lambda: called.append(True) or None
        )
        result = _resolve_trailers(("-m", "fix: something"))
        assert not called
        assert result is None

    def test_git_agent_set_skips_prompt(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        called = []
        monkeypatch.setattr(
            "co_authors.select_agent", lambda: called.append(True) or None
        )
        result = _resolve_trailers(())
        assert not called
        assert result == ("--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")

    def test_prompt_trailer_not_duplicated(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        monkeypatch.setattr("co_authors.select_agent", lambda: trailer)
        args = ("--trailer", trailer)
        result = _resolve_trailers(args)
        assert result is None
