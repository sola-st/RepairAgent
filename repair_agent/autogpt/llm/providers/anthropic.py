from __future__ import annotations

import functools
import time
from typing import Callable, List, Optional

from colorama import Fore
from autogpt.llm.base import (
    ChatModelInfo,
    MessageDict,
)
from autogpt.logs import logger

ANTHROPIC_CHAT_MODELS = {
    info.name: info
    for info in [
        ChatModelInfo(
            name="claude-sonnet-4-20250514",
            prompt_token_cost=0.003,   # $3/M
            completion_token_cost=0.015,  # $15/M
            max_tokens=200000,
            supports_functions=False,
        ),
        ChatModelInfo(
            name="claude-haiku-4-20250414",
            prompt_token_cost=0.0008,  # $0.80/M
            completion_token_cost=0.004,  # $4/M
            max_tokens=200000,
            supports_functions=False,
        ),
        ChatModelInfo(
            name="claude-opus-4-20250514",
            prompt_token_cost=0.015,   # $15/M
            completion_token_cost=0.075,  # $75/M
            max_tokens=200000,
            supports_functions=False,
        ),
    ]
}

# Aliases for convenience
anthropic_model_mapping = {
    "claude-sonnet": "claude-sonnet-4-20250514",
    "claude-haiku": "claude-haiku-4-20250414",
    "claude-opus": "claude-opus-4-20250514",
}

for alias, target in anthropic_model_mapping.items():
    if target in ANTHROPIC_CHAT_MODELS:
        alias_info = ChatModelInfo(**ANTHROPIC_CHAT_MODELS[target].__dict__)
        alias_info.name = alias
        ANTHROPIC_CHAT_MODELS[alias] = alias_info


def is_anthropic_model(model: str) -> bool:
    """Check if a model name refers to an Anthropic/Claude model."""
    return model.startswith("claude-")


def retry_api(
    max_retries: int = 10,
    backoff_base: float = 2.0,
    warn_user: bool = True,
):
    """Retry an Anthropic API call with exponential backoff."""

    def _wrapper(func: Callable):
        @functools.wraps(func)
        def _wrapped(*args, **kwargs):
            for attempt in range(1, max_retries + 2):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_name = type(e).__name__
                    # Retry on rate limit and server errors
                    if "RateLimitError" in error_name or "APIStatusError" in error_name:
                        if attempt >= max_retries + 1:
                            raise
                        backoff = backoff_base ** (attempt + 2)
                        logger.warn(
                            f"{Fore.RED}Anthropic API error: {e}. "
                            f"Waiting {backoff} seconds...{Fore.RESET}"
                        )
                        time.sleep(backoff)
                    else:
                        raise

        return _wrapped

    return _wrapper


@retry_api()
def create_chat_completion(
    messages: List[MessageDict],
    *_,
    **kwargs,
) -> dict:
    """Create a chat completion using the Anthropic API.

    Converts OpenAI-style messages to Anthropic format, calls the API,
    and returns a response in a structure compatible with the rest of the codebase.
    """
    try:
        import anthropic
    except ImportError:
        raise ImportError(
            "The 'anthropic' package is required for Claude models. "
            "Install it with: pip install anthropic"
        )

    import os

    api_key = kwargs.pop("api_key", None) or os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY is not set. Please set it as an environment variable "
            "or provide it via set_api_key.py."
        )

    model = kwargs.pop("model", "claude-sonnet-4-20250514")
    temperature = kwargs.pop("temperature", 0)
    max_tokens = kwargs.pop("max_tokens", 4096)

    # Remove OpenAI-specific kwargs that don't apply to Anthropic
    kwargs.pop("api_base", None)
    kwargs.pop("organization", None)
    kwargs.pop("functions", None)
    kwargs.pop("response_format", None)

    # Resolve aliases
    if model in anthropic_model_mapping:
        model = anthropic_model_mapping[model]

    # Convert messages: separate system message from conversation
    system_content = ""
    conversation = []
    for msg in messages:
        if msg["role"] == "system":
            system_content += msg["content"] + "\n"
        elif msg["role"] == "function":
            # Convert function messages to user messages
            conversation.append({"role": "user", "content": f"[Function result]: {msg['content']}"})
        else:
            conversation.append({"role": msg["role"], "content": msg["content"]})

    # Anthropic requires alternating user/assistant messages.
    # Merge consecutive messages of the same role.
    merged = []
    for msg in conversation:
        if merged and merged[-1]["role"] == msg["role"]:
            merged[-1]["content"] += "\n" + msg["content"]
        else:
            merged.append(dict(msg))

    # Ensure conversation starts with a user message
    if merged and merged[0]["role"] != "user":
        merged.insert(0, {"role": "user", "content": "Begin."})

    # Ensure max_tokens is positive
    max_tokens = max(1, min(max_tokens, 4096))

    client = anthropic.Anthropic(api_key=api_key)

    create_kwargs = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": merged,
    }
    if system_content.strip():
        create_kwargs["system"] = system_content.strip()

    response = client.messages.create(**create_kwargs)

    # Track usage
    from autogpt.llm.api_manager import ApiManager
    api_manager = ApiManager()
    api_manager.update_cost(
        response.usage.input_tokens,
        response.usage.output_tokens,
        model,
    )

    # Convert to OpenAI-compatible response structure
    content = ""
    for block in response.content:
        if hasattr(block, "text"):
            content += block.text

    logger.debug(f"Anthropic Response: {content[:500]}...")

    # Return a dict-like object that mimics OpenAI's response structure
    return _AnthropicResponse(
        content=content,
        model=model,
        usage=_Usage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        ),
    )


class _Usage:
    """Mimics OpenAI's usage object."""
    def __init__(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class _AnthropicResponse:
    """Mimics OpenAI's ChatCompletion response structure for compatibility."""

    def __init__(self, content: str, model: str, usage: _Usage):
        self.model = model
        self.usage = usage
        self.choices = [_Choice(content)]

    def __contains__(self, key):
        return hasattr(self, key)


class _Choice:
    """Mimics OpenAI's Choice object."""

    def __init__(self, content: str):
        self.message = {
            "role": "assistant",
            "content": content,
            "function_call": None,
        }
