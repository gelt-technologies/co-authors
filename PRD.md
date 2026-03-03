# co-authors — Product Requirements Document

## Overview

`co-authors` is a Python CLI tool that wraps the `git` client (via shell alias) to automatically append `Co-Authored-By` trailers to commit messages when coding agents are involved. It ensures attribution is correct and consistent without getting in the user's way.

---

## Problem Statement

When using AI coding agents (e.g. Claude Code, GitHub Copilot, Cursor), commits are often made without proper attribution to the agent. The `Co-Authored-By` git trailer is a widely-recognised convention for crediting co-authors, but there is no standard tooling to apply it automatically based on which agent is active.

---

## Goals

- Automatically append the correct `Co-Authored-By` trailer when committing with a known agent active.
- Never duplicate a trailer that already exists in the message.
- Be invisible and automatic in the normal workflow.
- Fall back to an interactive prompt when the agent is ambiguous (no `GIT_AGENT` set and no `-m` message supplied).
- Pass all unrecognised `git` subcommands and flags through to the real `git` binary unchanged.

---

## Non-Goals

- Replacing or reimplementing `git` beyond commit attribution.
- Managing git configuration (user name, email, remotes, etc.).
- Supporting non-`commit` git subcommands with special logic.

---

## Design

### Shell Alias

The user adds a shell alias so that `git` is transparently proxied through `co-authors`:

```bash
alias git="co-authors"
```

### Agent Registry

A built-in map of known agents to their `Co-Authored-By` strings:

| Agent key | Co-Authored-By trailer                                   |
| --------- | -------------------------------------------------------- |
| `claude`  | `Co-Authored-By: Claude <noreply@anthropic.com>`         |
| `copilot` | `Co-Authored-By: GitHub Copilot <copilot@github.com>`    |
| `cursor`  | `Co-Authored-By: Cursor <cursor@anysphere.io>`           |
| `gemini`  | `Co-Authored-By: Gemini Code Assist <gemini@google.com>` |

The registry should be extensible (future: user-defined agents in config).

### `GIT_AGENT` Environment Variable

When set, specifies the active agent key (e.g. `GIT_AGENT=claude`). This is the primary signal for automatic attribution.

### Behaviour Matrix

| Subcommand | `-m` flag | `GIT_AGENT` set | Behaviour                                                                  |
| ---------- | --------- | --------------- | -------------------------------------------------------------------------- |
| `commit`   | yes       | yes             | Append trailer via `--trailer` (unless already present). Pass through.     |
| `commit`   | yes       | no              | Pass through unchanged (no interactive prompt when message is explicit).   |
| `commit`   | no        | yes             | Append trailer via `--trailer`. Pass through.                              |
| `commit`   | no        | no              | Interactively prompt user to select an agent (or none). Then pass through. |
| other      | any       | any             | Pass all arguments through to `git` unchanged.                             |

### Trailer Injection

Use `git commit --trailer "Co-Authored-By: ..."` rather than editing the message string directly, to respect git's trailer formatting conventions.

If a `--trailer` argument with the same `Co-Authored-By` value is already present in the arguments (or already exists in the resolved commit message), skip injection to avoid duplicates.

### Interactive Agent Selection

When required, display a Rich-powered selection prompt listing all known agents plus a "None" option. The selection is not persisted — it applies only to the current commit.

---

## Technical Stack

| Concern        | Library                                  |
| -------------- | ---------------------------------------- |
| User prompts   | [rich](https://rich.readthedocs.io/)     |
| Python version | ≥ 3.14 (as per `pyproject.toml`)         |
| Packaging      | `uv` / `uv_build`                        |
| Entry point    | `co-authors` (maps to `co_authors:main`) |
