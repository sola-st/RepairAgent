""" A module for generating custom prompt strings."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from autogpt.models.command_registry import CommandRegistry


class PromptGenerator:
    """
    A class for generating custom prompt strings based on constraints, commands,
        resources, and performance evaluations.
    """

    @dataclass
    class Command:
        label: str
        name: str
        params: dict[str, str]
        function: Optional[Callable]

        def __str__(self) -> str:
            """Returns a string representation of the command."""
            params_string = ", ".join(
                f'"{key}": "{value}"' for key, value in self.params.items()
            )
            return f'{self.label}: "{self.name}", params: ({params_string})'

    commands: list[Command]
    command_registry: CommandRegistry | None


    def __init__(self):
        self.commands = []
        self.command_registry = None
        #self.simple_patterns = []
        self.general_guidelines: list[str] = []

    def add_simple_pattern(self, pattern: str) -> None:
        self.simple_patterns.append(pattern)

    def add_general_guidelines(self, line:str) -> None:
        self.general_guidelines.append(line)

    def add_command(
        self,
        command_label: str,
        command_name: str,
        params: dict[str, str] = {},
        function: Optional[Callable] = None,
    ) -> None:
        """
        Add a command to the commands list with a label, name, and optional arguments.

        *Should only be used by plugins.* Native commands should be added
        directly to the CommandRegistry.

        Args:
            command_label (str): The label of the command.
            command_name (str): The name of the command.
            params (dict, optional): A dictionary containing argument names and their
              values. Defaults to None.
            function (callable, optional): A callable function to be called when
                the command is executed. Defaults to None.
        """

        self.commands.append(
            PromptGenerator.Command(
                label=command_label,
                name=command_name,
                params={name: type for name, type in params.items()},
                function=function,
            )
        )

    def _generate_numbered_list(self, items: list[str], start_at: int = 1) -> str:
        """
        Generate a numbered list containing the given items.

        Args:
            items (list): A list of items to be numbered.
            start_at (int, optional): The number to start the sequence with; defaults to 1.

        Returns:
            str: The formatted numbered list.
        """
        return "\n".join(f"{i}. {item}" for i, item in enumerate(items, start_at))

    def generate_prompt_string(
        self,
        *,
        additional_simple_patterns: list[str] = [],
        additional_guidelines: list[str] = []
    ) -> str:
        """
        Generate a prompt string based on the constraints, commands, resources,
            and best practices.

        Returns:
            str: The generated prompt string.
        """
        with open("fix_format") as ffmt:
            fix_format = ffmt.read()
        return {
            "commands": [
                "## Commands",
                "You have access to the following commands (EXCLUSIVELY):",
                f"{self._generate_commands()}",
            ],
            "general guidelines":[
                "## General guidelines:",
                "Try to adhere to the following guidlines to the best of your ability:",
                f"{self._generate_numbered_list(self.general_guidelines + additional_guidelines)}",
            ],
            "fix format": [
                "## The format of the fix",
                "This is the description of the json format in which you should write your fixes (respect this format when calling the commands write_fix and try_fixes):",
                fix_format
            ]
        }

    def _generate_commands(self) -> str:
        command_strings = []
        if self.command_registry:
            command_strings += [
                str(cmd)
                for cmd in self.command_registry.commands.values()
                if cmd.enabled
            ]

        # Add commands from plugins etc.
        command_strings += [str(cmd) for cmd in self.commands]

        return self._generate_numbered_list(command_strings)
