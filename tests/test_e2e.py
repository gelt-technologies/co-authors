"""
End-to-end alias-simulation tests.

Each test covers one row of the behaviour matrix:

| Subcommand | -m flag | GIT_AGENT set | Expected behaviour                                      |
|------------|---------|---------------|---------------------------------------------------------|
| commit     | yes     | yes           | Trailer injected via --trailer; passed to git           |
| commit     | yes     | no            | Passed through unchanged (no prompt)                    |
| commit     | no      | yes           | Trailer injected via --trailer; passed to git           |
| commit     | no      | no            | Prompt shown; selection injected (or not if None)       |
| other      | any     | any           | All args forwarded to git unchanged                     |
"""

import sys

import pytest

from co_authors import main


def _run_main(monkeypatch, exec_calls, select_agent_return=None):
    """Helper: patch sys.argv, _exec_git, and select_agent, then call main()."""
    monkeypatch.setattr("co_authors._exec_git", lambda *args: exec_calls.append(args))
    if select_agent_return is not None:
        monkeypatch.setattr("co_authors.select_agent", lambda: select_agent_return)
    else:
        monkeypatch.setattr("co_authors.select_agent", lambda: None)


class TestCommitWithMessageAndAgent:
    def test_trailer_is_injected(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        calls = []
        _run_main(monkeypatch, calls)
        main("commit", "-m", "fix: something")
        assert len(calls) == 1
        args = calls[0]
        assert args == ("commit", "-m", "fix: something", "--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")

    def test_no_duplicate_trailer(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        calls = []
        _run_main(monkeypatch, calls, select_agent_return=trailer)
        main("commit", "-m", "fix: something", "--trailer", trailer)
        args = calls[0]
        assert args.count(trailer) == 1


class TestCommitWithMessageNoAgent:
    def test_no_trailer_injected(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        prompt_called = []
        calls = []
        monkeypatch.setattr("co_authors._exec_git", lambda *args: calls.append(args))
        monkeypatch.setattr(
            "co_authors.select_agent", lambda: prompt_called.append(True) or None
        )
        main("commit", "-m", "fix: something")
        assert not prompt_called
        assert "--trailer" not in calls[0]

    def test_original_args_preserved(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        calls = []
        _run_main(monkeypatch, calls)
        main("commit", "-m", "fix: something")
        assert calls[0] == ("commit", "-m", "fix: something")


class TestCommitNoMessageWithAgent:
    def test_trailer_injected(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "cursor")
        calls = []
        _run_main(monkeypatch, calls)
        main("commit", "--amend")
        args = calls[0]
        assert args == ("commit", "--amend", "--trailer", "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>")

    def test_prompt_not_called(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        prompt_called = []
        calls = []
        monkeypatch.setattr("co_authors._exec_git", lambda *args: calls.append(args))
        monkeypatch.setattr(
            "co_authors.select_agent", lambda: prompt_called.append(True) or None
        )
        main("commit", "--amend")
        assert not prompt_called


class TestCommitNoMessageNoAgent:
    def test_prompt_called_and_trailer_injected(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        calls = []
        _run_main(
            monkeypatch,
            calls,
            select_agent_return="Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>",
        )
        main("commit")
        args = calls[0]
        assert "--trailer" in args
        assert "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>" in args

    def test_prompt_none_selection_no_trailer(self, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        calls = []
        _run_main(monkeypatch, calls, select_agent_return=None)
        main("commit")
        assert "--trailer" not in calls[0]


class TestNonCommitPassThrough:
    @pytest.mark.parametrize(
        "argv",
        [
            ["status"],
            ["log", "--oneline"],
            ["push", "origin", "main"],
            ["diff", "--staged"],
            [],
        ],
    )
    def test_args_forwarded_unchanged(self, argv, monkeypatch):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        calls = []
        _run_main(monkeypatch, calls)
        main(*argv)
        assert len(calls) == 1
        assert calls[0] == tuple(argv)

    def test_git_agent_set_does_not_affect_non_commit(self, monkeypatch):
        monkeypatch.setenv("GIT_AGENT", "claude")
        calls = []
        _run_main(monkeypatch, calls)
        main("status")
        assert calls[0] == ("status",)
        assert "--trailer" not in calls[0]
