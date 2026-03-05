import pytest

from co_authors import _parse_co_authors_flags, _resolve_trailers, _trailer_present


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

    def test_me_flag_suppresses_trailer(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        assert _resolve_trailers((), me=True) is None

    def test_agent_override_used_instead_of_env(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "cursor")
        result = _resolve_trailers(("-m", "fix"), agent_override="claude")
        assert result == ("--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")

    def test_agent_override_without_env(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        result = _resolve_trailers(("-m", "fix"), agent_override="claude")
        assert result == ("--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")


class TestParseCoAuthorsFlags:
    def test_me_flag_sets_me_true(self):
        args, me, agent_override = _parse_co_authors_flags(("--me", "-m", "fix"))
        assert me is True
        assert args == ("-m", "fix")
        assert agent_override is None

    def test_agent_flag_space_form(self):
        args, me, agent_override = _parse_co_authors_flags(("--agent", "claude", "-m", "fix"))
        assert agent_override == "claude"
        assert args == ("-m", "fix")
        assert me is False

    def test_agent_flag_equals_form(self):
        args, me, agent_override = _parse_co_authors_flags(("--agent=claude", "-m", "fix"))
        assert agent_override == "claude"
        assert args == ("-m", "fix")
        assert me is False

    def test_other_args_untouched(self):
        args, me, agent_override = _parse_co_authors_flags(("-m", "fix: something", "--amend"))
        assert args == ("-m", "fix: something", "--amend")
        assert me is False
        assert agent_override is None

    def test_me_flag_alone(self):
        args, me, agent_override = _parse_co_authors_flags(("--me",))
        assert me is True
        assert args == ()

    def test_agent_flag_at_end_without_value_errors(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            _parse_co_authors_flags(("--agent",))
        assert exc_info.value.code == 1
        assert "co-authors: --agent requires a value" in capsys.readouterr().err

    def test_empty_args(self):
        args, me, agent_override = _parse_co_authors_flags(())
        assert args == ()
        assert me is False
        assert agent_override is None
