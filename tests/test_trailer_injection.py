from co_authors import _resolve_trailers, _trailer_present


class TestTrailerPresent:
    def test_not_present_empty_args(self):
        assert not _trailer_present(
            (), "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        )

    def test_not_present_unrelated_args(self):
        args = ("-m", "fix: something")
        assert not _trailer_present(
            args, "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        )

    def test_present_as_separate_arg(self):
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        args = ("--trailer", trailer, "-m", "fix: something")
        assert _trailer_present(args, trailer)

    def test_present_as_equals_form(self):
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        args = (f"--trailer={trailer}",)
        assert _trailer_present(args, trailer)

    def test_different_trailer_not_matched(self):
        args = ("--trailer", "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>")
        assert not _trailer_present(
            args, "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        )

    def test_trailer_flag_at_end_without_value(self):
        # --trailer at the very end with no following value should not crash
        args = ("--trailer",)
        assert not _trailer_present(
            args, "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        )


class TestResolveTrailers:
    def test_no_git_agent_returns_no_trailer(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        args = ("-m", "fix: something")
        assert _resolve_trailers(args) is None

    def test_known_agent_injects_trailer(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        result = _resolve_trailers(("-m", "fix: something"))
        assert result == ("--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")

    def test_unknown_agent_returns_no_trailer(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "unknown-agent")
        args = ("-m", "fix: something")
        assert _resolve_trailers(args) is None

    def test_no_trailer_when_trailer_already_present(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        args = ("--trailer", trailer, "-m", "fix: something")
        result = _resolve_trailers(args)
        assert result is None

    def test_no_duplicate_equals_form(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        args = (f"--trailer={trailer}",)
        result = _resolve_trailers(args)
        assert result is None

    def test_case_insensitive_agent_key(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "CLAUDE")
        result = _resolve_trailers(())
        assert result == ("--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")

    def test_cursor_agent(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "cursor")
        result = _resolve_trailers(())
        assert result == ("--trailer", "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>")
