from rich.console import Console
from rich.theme import Theme

custom_theme = Theme(
    {
        "r2n.dim": "dim",
        "r2n.muted": "bright_black",
        "r2n.accent": "cyan",
        "r2n.value": "white",
        "r2n.ok": "green",
        "r2n.fail": "red",
        "r2n.warn": "yellow",
        "r2n.subtle": "dim white",
        "info": "dim cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "highlight": "bold cyan",
    }
)

console = Console(theme=custom_theme)
