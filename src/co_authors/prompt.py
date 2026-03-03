from rich.console import Console
from rich.prompt import Prompt
from rich.markup import escape

from co_authors.agents import AGENTS

console = Console()


def select_agent() -> str | None:
    """Interactively prompt the user to select an agent. Returns the trailer string or None."""
    agent_keys = list(AGENTS.keys())

    console.print("\n[bold][white]Select a co-author agent:[/white][/bold]")
    for i, key in enumerate(agent_keys, start=1):
        console.print(f"  [cyan]{i}[/cyan]. [white]{escape(AGENTS[key])}[/white]")
    console.print("  [cyan]0[/cyan]. [white]None[/white]")

    choice = Prompt.ask(
        choices=["0", *[str(i) for i in range(1, len(agent_keys) + 1)]],
        default="0",
    )

    index = int(choice)
    if index == 0:
        return None

    key = agent_keys[index - 1]
    return f"Co-Authored-By: {AGENTS[key]}"
