import signal
import subprocess
import sys
from os import environ

from co_authors.agents import get_trailer
from co_authors.prompt import select_agent


def _exec_git(*args: str) -> int:
    """Run the real git binary with the given arguments and propagate its exit code."""
    try:
        proc = subprocess.Popen(["git", *args])
    except FileNotFoundError:
        print("co-authors: git not found in PATH", file=sys.stderr)
        return 1

    def _forward(signum, frame):
        proc.send_signal(signum)

    original_sigint = signal.signal(signal.SIGINT, _forward)
    original_sigterm = signal.signal(signal.SIGTERM, _forward)
    try:
        proc.wait()
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)
    return proc.returncode


def _trailer_present(args: tuple[str, ...], trailer: str) -> bool:
    """Return True if the trailer value is already present in args."""
    for i, arg in enumerate(args):
        if arg == "--trailer" and i + 1 < len(args) and args[i + 1] == trailer:
            return True
        if arg == f"--trailer={trailer}":
            return True
    return False


def _has_message_flag(args: tuple[str, ...]) -> bool:
    """Return True if -m or --message is present in args."""
    return "-m" in args or "--message" in args


def _no_editor_needed(args: tuple[str, ...]) -> bool:
    """Return True if git commit will not open an editor."""
    return _has_message_flag(args) or "--no-edit" in args


def _resolve_trailers(args: tuple[str, ...]) -> tuple[str, ...]:
    """Inject a Co-Authored-By trailer based on GIT_AGENT or interactive prompt."""
    agent_key = environ.get("GIT_AGENT", "")

    if agent_key:
        trailer = get_trailer(agent_key)
    elif not _has_message_flag(args):
        trailer = select_agent()
    else:
        return None

    if trailer and not _trailer_present(args, trailer):
       return ("--trailer", trailer)

    return None


def commit(*args: str) -> None:
    """Run git commit, automatically adding Co-Authored-By trailers."""
    trailer = _resolve_trailers(args)

    if trailer is None:
        return _exec_git("commit", *args)

    if _no_editor_needed(args):
        return _exec_git("commit", *args, *trailer)

    # Commit first so the editor shows a clean template, then amend to add
    code = _exec_git("commit", *args)

    if code == 0:
        return _exec_git("commit", "--amend", "--no-edit", *trailer)
    else:
        return code


def main(*args: str) -> int:
    argv = args or sys.argv[1:]
    if not argv or argv[0] != "commit":
        return _exec_git(*argv)
    return commit(*argv[1:]) or 0


def cli() -> None:
    sys.exit(main())
