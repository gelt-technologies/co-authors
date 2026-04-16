import subprocess
import textwrap

from conftest import run_co_authors


class TestHookNotCalledTwiceOnAmend:
    def test_commit_msg_hook_runs_once(self, git_repo, git_env, tmp_path):
        subprocess.run(
            ["git", "checkout", "-b", "feature/proj-123-add-thing"],
            cwd=git_repo,
            env=git_env,
            check=True,
            capture_output=True,
        )

        call_log = git_repo / ".git" / "hook-calls.txt"
        hook = git_repo / ".git" / "hooks" / "commit-msg"
        hook.write_text(f"#!/bin/sh\necho called >> {call_log}\n")
        hook.chmod(0o755)

        editor = tmp_path / "editor.sh"
        editor.write_text("#!/bin/sh\necho 'add some feature' > \"$1\"\n")
        editor.chmod(0o755)

        (git_repo / "file.txt").write_text("change")
        subprocess.run(
            ["git", "add", "file.txt"],
            cwd=git_repo,
            env=git_env,
            check=True,
            capture_output=True,
        )

        env = {**git_env, "GIT_AGENT": "claude", "GIT_EDITOR": str(editor)}
        run_co_authors(git_repo, ["commit"], env=env)

        calls = call_log.read_text().strip().splitlines()
        assert len(calls) == 1, f"commit-msg hook fired {len(calls)} times, expected 1"

    def test_no_duplicate_ticket_in_commit_message(self, git_repo, git_env, tmp_path):
        subprocess.run(
            ["git", "checkout", "-b", "feature/proj-123-add-thing"],
            cwd=git_repo,
            env=git_env,
            check=True,
            capture_output=True,
        )

        hook = git_repo / ".git" / "hooks" / "commit-msg"
        hook.write_text(
            textwrap.dedent("""\
            #!/bin/sh
            branch_ticket=$(git branch --show-current | grep -io '[A-Z]\\+-[0-9]*' | head -n 1 | awk '{print toupper($0)}')
            commit_ticket=$(cat $1 | grep -io "[A-Z]\\+-[0-9]*")
            if [ -z $branch_ticket ]; then exit 0; fi
            if [ ! -z $commit_ticket ]; then exit 0; fi
            echo "$branch_ticket - $(cat $1)" > $1
        """)
        )
        hook.chmod(0o755)

        editor = tmp_path / "editor.sh"
        editor.write_text("#!/bin/sh\necho 'add some feature' > \"$1\"\n")
        editor.chmod(0o755)

        (git_repo / "file.txt").write_text("change")
        subprocess.run(
            ["git", "add", "file.txt"],
            cwd=git_repo,
            env=git_env,
            check=True,
            capture_output=True,
        )

        env = {**git_env, "GIT_AGENT": "claude", "GIT_EDITOR": str(editor)}
        run_co_authors(git_repo, ["commit"], env=env)

        log = subprocess.run(
            ["git", "log", "--format=%B", "-n", "1"],
            cwd=git_repo,
            env=git_env,
            capture_output=True,
            text=True,
        )
        assert log.stdout.count("PROJ-123") == 1
