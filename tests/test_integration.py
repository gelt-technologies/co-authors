"""
Real E2E integration tests.

Each test invokes the actual ``co-authors`` binary against a real git repository
(provided by the ``git_repo`` fixture) and verifies behaviour by inspecting
``git log`` output.
"""

import signal
import subprocess
import time

import pytest

from conftest import run_co_authors


def _stage_new_file(repo_path, env, filename="change.txt", content="hello\n"):
    """Write a file and stage it so a commit can be made."""
    (repo_path / filename).write_text(content)
    subprocess.run(
        ["git", "add", filename], cwd=repo_path, check=True, capture_output=True, env=env
    )


def _last_commit_message(repo_path, env):
    """Return the full commit message of the most recent commit."""
    result = subprocess.run(
        ["git", "log", "-1", "--format=%B"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    return result.stdout


class TestCommitWithMessageAndAgent:
    def test_trailer_in_git_log(self, git_repo, git_env):
        _stage_new_file(git_repo, git_env)
        result = run_co_authors(
            git_repo,
            ["commit", "-m", "feat: add change"],
            env={**git_env, "GIT_AGENT": "claude"},
        )
        assert result.returncode == 0, result.stderr
        log = _last_commit_message(git_repo, git_env)
        assert "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>" in log


class TestCommitNoMessageWithAgent:
    def test_trailer_in_git_log(self, git_repo, git_env):
        _stage_new_file(git_repo, git_env)
        result = run_co_authors(
            git_repo,
            ["commit"],
            env={**git_env, "GIT_AGENT": "cursor", "GIT_EDITOR": "true"},
        )
        assert result.returncode == 0, result.stderr
        log = _last_commit_message(git_repo, git_env)
        assert "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>" in log


class TestCommitWithMessageNoAgent:
    def test_no_trailer_in_git_log(self, git_repo, git_env):
        env = {k: v for k, v in git_env.items() if k != "GIT_AGENT"}
        _stage_new_file(git_repo, env)
        result = run_co_authors(
            git_repo,
            ["commit", "-m", "feat: plain commit"],
            env=env,
        )
        assert result.returncode == 0, result.stderr
        log = _last_commit_message(git_repo, env)
        assert "Co-Authored-By:" not in log


class TestNoDuplicateTrailer:
    def test_trailer_appears_once(self, git_repo, git_env):
        _stage_new_file(git_repo, git_env)
        trailer = "Co-Authored-By: Claude <claude[bot]@users.noreply.github.com>"
        result = run_co_authors(
            git_repo,
            ["commit", "-m", "feat: add change", "--trailer", trailer],
            env={**git_env, "GIT_AGENT": "claude"},
        )
        assert result.returncode == 0, result.stderr
        log = _last_commit_message(git_repo, git_env)
        assert log.count(trailer) == 1


class TestNonCommitPassthrough:
    def test_status_exits_zero(self, git_repo, git_env):
        result = run_co_authors(
            git_repo,
            ["status"],
            env={**git_env, "GIT_AGENT": "claude"},
        )
        assert result.returncode == 0, result.stderr
        assert "Co-Authored-By:" not in result.stdout
        assert "Co-Authored-By:" not in result.stderr

    def test_log_oneline_exits_zero(self, git_repo, git_env):
        result = run_co_authors(
            git_repo,
            ["log", "--oneline"],
            env={**git_env, "GIT_AGENT": "claude"},
        )
        assert result.returncode == 0, result.stderr
        assert "Co-Authored-By:" not in result.stdout
        assert "Co-Authored-By:" not in result.stderr


class TestCommitAmendWithAgent:
    def test_trailer_in_amended_commit(self, git_repo, git_env):
        result = run_co_authors(
            git_repo,
            ["commit", "--amend", "--no-edit"],
            env={**git_env, "GIT_AGENT": "cursor"},
        )
        assert result.returncode == 0, result.stderr
        log = _last_commit_message(git_repo, git_env)
        assert "Co-Authored-By: Cursor <cursor[bot]@users.noreply.github.com>" in log


class TestSigintForwarding:
    def test_sigint_exits_nonzero(self, git_repo, git_env):
        _stage_new_file(git_repo, git_env, filename="sigint_test.txt")
        proc = subprocess.Popen(
            ["co-authors", "commit"],
            cwd=git_repo,
            env={**git_env, "GIT_AGENT": "claude", "GIT_EDITOR": "sleep 60"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        time.sleep(0.5)  # allow git + editor to start
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail("co-authors did not exit after SIGINT within 5 s")
        assert proc.returncode != 0
