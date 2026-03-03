import functools
import os
import subprocess

import pytest


def run_co_authors(repo_path, args, env=None):
    """Run the co-authors binary as a subprocess inside repo_path.

    The provided env dict is used as-is (callers are expected to pass a fully
    merged environment, e.g. from the ``git_env`` fixture).
    Falls back to the current environment if no env is provided.
    Returns the completed ``subprocess.CompletedProcess`` so callers can
    inspect returncode, stdout, and stderr.
    """
    full_env = env if env is not None else os.environ.copy()
    return subprocess.run(
        ["co-authors", *args],
        cwd=repo_path,
        env=full_env,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def git_env(tmp_path):
    """Return an isolated git environment dict.

    Sets GIT_CONFIG_NOSYSTEM=1 and points HOME at a temp directory so that
    commit signing, GPG, and other user-level settings cannot interfere.
    """
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    return {
        **os.environ,
        "HOME": str(fake_home),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
    }


@pytest.fixture
def git_repo(tmp_path, git_env):
    """Initialise a git repo with an initial commit so HEAD exists.

    Returns the repo path. Use the ``git_env`` fixture to access the isolated
    environment for subsequent git or co-authors calls.
    """
    git = functools.partial(
        subprocess.run,
        cwd=tmp_path,
        env=git_env,
        check=True,
        capture_output=True,
    )

    git(["git", "init"])
    git(["git", "config", "user.name", "Test User"])
    git(["git", "config", "user.email", "test@example.com"])
    (tmp_path / "README.md").write_text("# test\n")
    git(["git", "add", "README.md"])
    git(["git", "commit", "-m", "Initial commit"])
    return tmp_path
