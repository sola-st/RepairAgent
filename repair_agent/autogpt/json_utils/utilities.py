"""Utilities for the json_fixes package."""
import ast
import json
import os.path
from typing import Any, Literal

from jsonschema import Draft7Validator

from autogpt.config import Config
from autogpt.logs import logger

LLM_DEFAULT_RESPONSE_FORMAT = "llm_response_format_1"


def extract_dict_from_response(response_content: str) -> dict[str, Any]:
    # Sometimes the response includes the JSON in a code block with ```
    start_triple_quote = response_content.find("```")
    if start_triple_quote != -1:
        response_content = response_content[start_triple_quote:]
        end_triple_quote = response_content[3:].find("```")
        if end_triple_quote != -1:
            response_content = response_content[:end_triple_quote+3]
            if response_content.startswith('json'):
                response_content = response_content[4:]
            response_content = "\n".join(response_content.split("\n")[1:])
            
        """if response_content.startswith("```") and response_content.endswith("```"):
            response_content = response_content.split("\n")[1:]
            for i in range(len(response_content)-1, 0, -1):
                if response_content[i]=="```":
                    response_content = response_content[:i]
                    break
            response_content = "\n".join(response_content)"""
            # Discard the first and last ```, then re-join in case the response naturally included ```
            #response_content = "```".join(response_content.split("```")[1:-1])

    # response content comes from OpenAI as a Python `str(content_dict)`, literal_eval reverses this
    try:
        return ast.literal_eval(response_content)
    except BaseException as e:
        with open("response_content.txt", "w") as rct:
            rct.write(response_content)
        logger.info(f"Error parsing JSON response with literal_eval {e}")
        logger.debug(f"Invalid JSON received in response: {response_content}")
        # TODO: How to raise an error here without causing the program to exit?
        return {}


def llm_response_schema(
    config: Config, schema_name: str = LLM_DEFAULT_RESPONSE_FORMAT
) -> dict[str, Any]:
    filename = os.path.join(os.path.dirname(__file__), f"{schema_name}.json")
    with open(filename, "r") as f:
        try:
            json_schema = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load JSON schema: {e}")
    if config.openai_functions:
        del json_schema["properties"]["command"]
        json_schema["required"].remove("command")
    return json_schema


def validate_dict(
    object: object, config: Config, schema_name: str = LLM_DEFAULT_RESPONSE_FORMAT
) -> tuple[Literal[True], None] | tuple[Literal[False], list]:
    """
    :type schema_name: object
    :param schema_name: str
    :type json_object: object

    Returns:
        bool: Whether the json_object is valid or not
        list: Errors found in the json_object, or None if the object is valid
    """
    schema = llm_response_schema(config, schema_name)
    validator = Draft7Validator(schema)

    if errors := sorted(validator.iter_errors(object), key=lambda e: e.path):
        for error in errors:
            logger.debug(f"JSON Validation Error: {error}")

        if config.debug_mode:
            logger.error(json.dumps(object, indent=4))
            logger.error("The following issues were found:")

            for error in errors:
                logger.error(f"Error: {error.message}")
        return False, errors

    logger.debug("The JSON object is valid.")

    return True, None
