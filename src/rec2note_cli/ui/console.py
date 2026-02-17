from rich.console import Console
from rich.theme import Theme

# Custom theme for semantic coloring
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "error": "bold red",
    "success": "bold green",
    "highlight": "bold yellow"
})

# Export this console object to be used everywhere
console = Console(theme=custom_theme)
