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

import pytest

from co_authors import main


@pytest.fixture
def git_calls(monkeypatch):
    calls = []
    monkeypatch.setattr("co_authors._exec_git", lambda *args: calls.append(args))
    return calls


class TestCommitWithMessageAndAgent:
    def test_trailer_is_injected(self, monkeypatch, git_calls):
        monkeypatch.setenv("GIT_AGENT", "claude")
        main("commit", "-m", "fix: something")
        assert git_calls[0] == ("commit", "-m", "fix: something", "--trailer", "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>")

    def test_no_duplicate_trailer(self, monkeypatch, git_calls):
        monkeypatch.setenv("GIT_AGENT", "claude")
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        main("commit", "-m", "fix: something", "--trailer", trailer)
        assert git_calls[0].count(trailer) == 1


class TestCommitWithMessageNoAgent:
    def test_no_trailer_injected(self, monkeypatch, git_calls):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        prompt_called = []
        monkeypatch.setattr("co_authors.select_agent", lambda: prompt_called.append(True) or None)
        main("commit", "-m", "fix: something")
        assert not prompt_called
        assert git_calls[0] == ("commit", "-m", "fix: something")

    def test_original_args_preserved(self, monkeypatch, git_calls):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        main("commit", "-m", "fix: something")
        assert git_calls[0] == ("commit", "-m", "fix: something")


class TestCommitNoMessageWithAgent:
    def test_trailer_injected(self, monkeypatch, git_calls):
        monkeypatch.setenv("GIT_AGENT", "cursor")
        main("commit", "--amend")
        assert git_calls[0] == ("commit", "--amend", "--trailer", "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>")

    def test_prompt_not_called(self, monkeypatch, git_calls):
        monkeypatch.setenv("GIT_AGENT", "claude")
        prompt_called = []
        monkeypatch.setattr("co_authors.select_agent", lambda: prompt_called.append(True) or None)
        main("commit", "--amend")
        assert not prompt_called


class TestCommitNoMessageNoAgent:
    def test_prompt_called_and_trailer_injected(self, monkeypatch, git_calls):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        monkeypatch.setattr("co_authors.select_agent", lambda: "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>")
        main("commit")
        assert "--trailer" in git_calls[0]
        assert "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>" in git_calls[0]

    def test_prompt_none_selection_no_trailer(self, monkeypatch, git_calls):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        monkeypatch.setattr("co_authors.select_agent", lambda: None)
        main("commit")
        assert "--trailer" not in git_calls[0]


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
    def test_args_forwarded_unchanged(self, argv, monkeypatch, git_calls):
        monkeypatch.delenv("GIT_AGENT", raising=False)
        main(*argv)
        assert len(git_calls) == 1
        assert git_calls[0] == tuple(argv)

    def test_git_agent_set_does_not_affect_non_commit(self, monkeypatch, git_calls):
        monkeypatch.setenv("GIT_AGENT", "claude")
        main("status")
        assert git_calls[0] == ("status",)
        assert "--trailer" not in git_calls[0]
