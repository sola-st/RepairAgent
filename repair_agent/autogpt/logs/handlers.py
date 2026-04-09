import json
import logging
import re
from pathlib import Path

from rich.console import Console


# Map colorama Fore.* ANSI escape codes to rich style names
_COLORAMA_TO_RICH = {
    "\x1b[30m": "black",
    "\x1b[31m": "red",
    "\x1b[32m": "green",
    "\x1b[33m": "yellow",
    "\x1b[34m": "blue",
    "\x1b[35m": "magenta",
    "\x1b[36m": "cyan",
    "\x1b[37m": "white",
    "\x1b[90m": "bright_black",
    "\x1b[91m": "bright_red",
    "\x1b[92m": "bright_green",
    "\x1b[93m": "bright_yellow",
    "\x1b[94m": "bright_blue",
    "\x1b[95m": "bright_magenta",
    "\x1b[96m": "bright_cyan",
    "\x1b[97m": "bright_white",
}

_ANSI_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def _colorama_to_rich_style(ansi_code: str) -> str:
    """Convert a colorama ANSI escape string to a rich style name."""
    return _COLORAMA_TO_RICH.get(ansi_code, "")


class ConsoleHandler(logging.StreamHandler):
    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        try:
            print(msg)
        except Exception:
            self.handleError(record)


class RichConsoleHandler(logging.StreamHandler):
    """Output to console using rich — instant rendering, no typing simulation."""

    def __init__(self):
        super().__init__()
        self.rich_console = Console(highlight=False)

    def emit(self, record: logging.LogRecord):
        try:
            title = getattr(record, "title", "")
            color = getattr(record, "color", "")
            msg = record.getMessage()

            # Strip any embedded ANSI codes from the message body
            clean_msg = _ANSI_RE.sub("", msg)

            # Handle blank-line calls like typewriter_log("\n")
            if not title and not clean_msg.strip():
                self.rich_console.print()
                return

            style = _colorama_to_rich_style(color)

            if title and clean_msg:
                self.rich_console.print(
                    f"[{style}]{title}[/{style}] {clean_msg}" if style
                    else f"{title} {clean_msg}"
                )
            elif title:
                self.rich_console.print(
                    f"[{style}]{title}[/{style}]" if style else title
                )
            else:
                self.rich_console.print(clean_msg)
        except Exception:
            self.handleError(record)


class JsonFileHandler(logging.FileHandler):
    def __init__(self, filename: str | Path, mode="a", encoding=None, delay=False):
        super().__init__(filename, mode, encoding, delay)

    def emit(self, record: logging.LogRecord):
        json_data = json.loads(self.format(record))
        with open(self.baseFilename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
