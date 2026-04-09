"""A spinner module using rich."""
from rich.console import Console


class Spinner:
    """A spinner class using rich's Status for animated feedback."""

    def __init__(
        self,
        message: str = "Loading...",
        delay: float = 0.1,
        plain_output: bool = False,
    ) -> None:
        self.plain_output = plain_output
        self.message = message
        self.running = False
        self._console = Console(highlight=False)
        self._status = None

    def start(self):
        self.running = True
        if self.plain_output:
            self._console.print(self.message)
            return
        self._status = self._console.status(self.message, spinner="dots")
        self._status.start()

    def stop(self):
        self.running = False
        if self._status is not None:
            self._status.stop()
            self._status = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        self.stop()
