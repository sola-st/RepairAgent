from autogpt.config.config import Config
from autogpt.config.prompt_config import PromptConfig
from autogpt.prompts.generator import PromptGenerator

DEFAULT_TRIGGERING_PROMPT = (
    "Determine exactly one command to use based on the given goals "
    "and the progress you have made so far, "
    "and respond using the JSON schema specified previously:"
)


def build_default_prompt_generator(config: Config) -> PromptGenerator:
    """
    This function generates a prompt string that includes various constraints,
        commands, resources, and best practices.

    Returns:
        str: The generated prompt string.
    """

    # Initialize the PromptGenerator object
    prompt_generator = PromptGenerator()

    # Initialize the PromptConfig object and load the file set in the main config (default: prompts_settings.yaml)
    prompt_config = PromptConfig(config.prompt_settings_file)

    for guideline in prompt_config.general_guidelines:
        prompt_generator.add_general_guidelines(guideline)

    #for pattern in prompt_config.simple_patterns:
    #    prompt_generator.add_simple_pattern(pattern)

    #for step in prompt_config.work_plan:
    #    prompt_generator.add_work_plan(step)
    return prompt_generator
