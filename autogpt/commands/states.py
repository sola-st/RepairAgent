COMMAND_CATEGORY = "states"
COMMAND_CATEGORY_TITLE = "STATES"
ALLOWLIST_CONTROL = "allowlist"
DENYLIST_CONTROL = "denylist"

from autogpt.command_decorator import command
from autogpt.agents.agent import Agent


@command(
        "express_hypothesis",
        "This command allows to express a hypothesis about what exactly is the bug. Call this command after you have collected enough information about the bug in the project",
        {
            "hypothesis":{
                "type": "string",
                "description": "The hypothesis that youo should express in text",
                "required": True
            }
        }
)
def express_hypothesis(hypothesis: str, agent: Agent) -> str:
    return "Since you have a hypothesis about the bug, the current state have been changed from 'collect information to understand the bug' to 'collect information to fix the bug'"

@command(
        "discard_hypothesis",
        "This command allows you to discard the hypothesis that you made earlier about the bug and automatically return back again to the state 'collect information to uderstand the bug' where you can express a new hypothesis",
        {
            "reason_for_discarding":{
                "type": "string",
                "description": "Give your reason for discarding the hypothesis",
                "required": True
            }
        }
)
def discard_hypothesis(reason_for_discarding: str, agent: Agent) -> str:
    return "Hypothesis discarded! You are now back at the state 'collect information to understand the bug'"

@command(
        "go_back_to_collect_more_info",
        "This command allows you to go back to the state 'collect information to fix the bug'. Call this command when you suggest many fixes but none of them work.",
        {
            "reason_for_going_back":{
                "type": "string",
                "description": "Give your reason for going back to a previous state",
                "required": True
            }
        }
)
def go_back_to_collect_more_info(reason_for_going_back: str, agent: Agent) -> str:
    return "You are now back at the state 'collect information to fix the bug'"


@command(
    "change_state",
    "this command allows you to change the current state based on info that you collected and the next steps that you want to make. As intput to this function, give the name of your current state and the name of the state that you want to switch to. Current state and next state should be two different states (cannot change to the same state).",
    {
        "next_state_name": {
            "type": "string",
            "description": "The name the next_state",
            "required": True,
        }
    },
)
def change_state(current_state:str, next_state_name: str, agent:Agent) -> str:
    change_possibilities = {
        "collect information to understand the bug": ["collect information to fix the bug"],
        "collect information to fix the bug":["trying out candidate fixes"],
        "trying out candidate fixes": ["collect information to understand the bug", "collect information to fix the bug"]
    }
    if current_state not in change_possibilities:
        return "Uknown current state, please provide the correct current state name"
    elif next_state_name not in change_possibilities[current_state]:
        return "Impossibel to switch state from {} to {}. It is not allowed.".format(current_state, next_state_name)
    else:
        return "State changed successfully."
    
"""
s1: collect information to understand the bug
s2: collect information to fix the bug
s3: trying out candidate fixes

s3 to s1: discard hypothesis
s3 to s2: need more info
"""

## TODO SAVE THE HYPOTHESIS IN THE PROMPT

