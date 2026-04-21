from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "r2n.dim": "dim",
        "r2n.muted": "bright_black",
        "r2n.key": "bold cyan",
        "r2n.value": "bright_green",
        "r2n.number": "bright_magenta",
        "r2n.accent": "cyan",
        "r2n.ok": "bold green",
        "r2n.fail": "bold red",
        "r2n.warn": "bright_yellow",
        "r2n.subtle": "dim white",
        "r2n.section": "bold magenta",
        "r2n.rule": "dim cyan",
        "info": "dim cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "highlight": "bold cyan",
    }
)

console = Console(theme=custom_theme)
