from __future__ import annotations

import re
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Literal, Optional
import json
import os

if TYPE_CHECKING:
    from autogpt.config import AIConfig, Config

    from autogpt.models.command_registry import CommandRegistry

from autogpt.llm.base import ChatModelResponse, ChatSequence, Message
from autogpt.llm.providers.openai import OPEN_AI_CHAT_MODELS, get_openai_command_specs
from autogpt.llm.utils import count_message_tokens, create_chat_completion
from autogpt.logs import logger
from autogpt.memory.message_history import MessageHistory
from autogpt.prompts.prompt import DEFAULT_TRIGGERING_PROMPT
from autogpt.json_utils.utilities import extract_dict_from_response
from autogpt.commands.defects4j_static import get_info, run_tests, query_for_fix, query_for_commands, extract_command, execute_command, create_fix_template

CommandName = str
CommandArgs = dict[str, str]
AgentThoughts = dict[str, Any]

class BaseAgent(metaclass=ABCMeta):
    """Base class for all Auto-GPT agents."""

    ThoughtProcessID = Literal["one-shot"]

    def __init__(
        self,
        ai_config: AIConfig,
        command_registry: CommandRegistry,
        config: Config,
        big_brain: bool = True,
        default_cycle_instruction: str = DEFAULT_TRIGGERING_PROMPT,
        cycle_budget: Optional[int] = 1,
        send_token_limit: Optional[int] = None,
        summary_max_tlength: Optional[int] = None,
        experiment_file: str = None
    ):
        self.experiment_file = experiment_file
        self.ai_config = ai_config
        """The AIConfig or "personality" object associated with this agent."""

        self.command_registry = command_registry
        """The registry containing all commands available to the agent."""

        self.config = config
        """The applicable application configuration."""

        self.big_brain = big_brain
        """
        Whether this agent uses the configured smart LLM (default) to think,
        as opposed to the configured fast LLM.
        """

        self.default_cycle_instruction = default_cycle_instruction
        """The default instruction passed to the AI for a thinking cycle."""

        self.cycle_budget = cycle_budget
        """
        The number of cycles that the agent is allowed to run unsupervised.

        `None` for unlimited continuous execution,
        `1` to require user approval for every step,
        `0` to stop the agent.
        """

        self.cycles_remaining = cycle_budget
        """The number of cycles remaining within the `cycle_budget`."""

        self.cycle_count = 0
        """The number of cycles that the agent has run since its initialization."""
        
        with open("commands_by_state.json") as cbs:
            self.cmds_by_state = json.load(cbs)

        with open("states_description.json") as sdj:
            self.descriptions = json.load(sdj)

        self.current_state = "collect information to understand the bug"
        self.prompt_dictionary = ai_config.construct_full_prompt(config)

        self.prompt_dictionary["commands"][2] = self.cmds_by_state[self.current_state]        
        self.prompt_dictionary["current state"] = self.descriptions[self.current_state]

        prompt_goal = self.prompt_dictionary["goals"][2]
        start_i = prompt_goal.find("bug within the project")
        end_i = len(prompt_goal)
        in_between = prompt_goal[start_i:end_i-1]
        try:
            self.project_name, self.bug_index= in_between.replace("bug within the project ", "").replace(' and bug index ', " ").replace('"', "").split(" ")[:2]
        except:
            print("PG:", self.prompt_dictionary["goals"][2])
        self.localization_info = get_info(self.project_name, self.bug_index,"auto_gpt_workspace")
        self.tests_results = run_tests(self.project_name, self.bug_index, "auto_gpt_workspace")
        """
        The system prompt sets up the AI's personality and explains its goals,
        available resources, and restrictions.
        """

        llm_name = self.config.smart_llm if self.big_brain else self.config.fast_llm
        self.llm = OPEN_AI_CHAT_MODELS[llm_name]
        """The LLM that the agent uses to think."""

        self.send_token_limit = send_token_limit or self.llm.max_tokens * 3 / 4
        """
        The token limit for prompt construction. Should leave room for the completion;
        defaults to 75% of `llm.max_tokens`.
        """

        self.history = MessageHistory(
            self.llm,
            max_summary_tlength=summary_max_tlength or self.send_token_limit // 6,
        )

        # These are new attributes used to construct the prompt
        """
        {
            "file_path":
                    {        self.ai_config = ai_config

                        (XX, YY): [...]
                    }
                
        }
        """
        self.read_files = {}

        """
        {
            "file_path": [
                {
                    "lines_range": (XX, YY),
                    "lines_list": [...]
                }
            ]
        }
        """
        self.suggested_fixes = {}

        """
        [
            {
                "query": [... list of search keywords],
                "result": dictionary of search result
            }
        ]
        """
        self.search_queries = []


        """
        {
            "get_info": "...",
            "run_tests": "...",
            "failing_test_code": "..."
        }
        """

        self.bug_report = {}
        self.commands_history = []
        self.human_feedback = []
        self.ask_chatgpt = None
        self.hypothesises = []

        ## Here we put the initial values for the collected context sections
        self.initial_bug_report = {

        }

        self.buggy_lines = ""
        self.similar_calls = None

        with open(experiment_file) as hper:
            self.hyperparams = json.load(hper)

        self.extracted_methods = []

        self.pre_search = ""
        self.pre_similar = ""
        self.pre_methods_code = ""

        self.suggested_commands = []

        self.auto_complete = True
        self. generated_methods= None
        self.dummy_fix = False
        with open("experimental_setups/experiments_list.txt") as eht:
            self.exps = eht.read().splitlines()

    def save_context(self,):
        return
        context = {
            "cycle_budget": self.cycle_budget,
            "cycle_count": self.cycle_count,
            "cycle_remaining": self.cycles_remaining,
            "current_state": self.current_state,
            "prompt_dictionary": self.prompt_dictionary,
            "project_name": self.project_name,
            "bug_index": self.bug_index,
            "localization_info": self.localization_info,
            "test_results": self.tests_results,
            "read_files": self.read_files,
            "suggested_fixes": self.suggested_fixes,
            "search_queries": self.search_queries,
            "bug_report": self.bug_report,
            "bug_index": self.bug_index,
            "commands_history": self.commands_history,
            "human_feedback": self.human_feedback ,
            "ask_chatgpt": self.ask_chatgpt,
            "hypothesises": self.hypothesises,
            "initial_bug_report": self.initial_bug_report,
            "buggy_lines": self.buggy_lines,
            "similar_calls": self.similar_calls,
            "extracted_methods": self.extracted_methods,
            "experiment_file": self.experiment_file,
            "hyperparams": self.hyperparams,
            "history": [{"role": msg.role, "content": msg.content} for _, msg in enumerate(self.history)]
        }

        #with open("experimental_setups/experiments_list.txt") as eht:
        exps =self.exps

        with open(os.path.join("experimental_setups", exps[-1], "saved_contexts", "saved_context_{}_{}".format(self.project_name, self.bug_index)), "w") as patf:
            json.dump(context, patf)
        

    def construct_pre_info(self, ):
        query = "I have a set of functions that help me analyze and repair buggy code. I will give you the description of the functions (I also call them commands), and the buggy piece of code and tell me what commands would make sense to call to get more info about the bug.\n"

        query += """## Commands
You have access to the following commands (EXCLUSIVELY):
1. search_code_base: This utility function scans all Java files within a specified project for a given list of keywords. It generates a dictionary as output, organized by file names, classes, and method names. Within each method name, it provides a list of keywords that match the method's content. The resulting structure is as follows: { file_name: { class_name: { method_name: [...list of matched keywords...] } } }. This functionality proves beneficial for identifying pre-existing methods that may be reusable or for locating similar code to gain insights into implementing specific functionalities. It's important to note that this function does not return the actual code but rather the names of matched methods containing at least one of the specified keywords. It requires the following params params: (project_name: string, bug_index: integer, key_words: list). Once the method names are obtained, the extract_method_code command can be used to retrieve their corresponding code snippets (only do it for the ones that are relevant)
2. get_classes_and_methods: This function allows you to get all classes and methods names within a file. It returns a dictinary where keys are classes names and values are list of methods names within each class. The required params are: (project_name: string, bug_index: integer, file_path: string)
3. extract_similar_functions_calls: For a provided buggy code snippet in 'code_snippet' within the file 'file_path', this function extracts similar function calls. This aids in understanding how functions are utilized in comparable code snippets, facilitating the determination of appropriate parameters to pass to a function., params: (project_name: string, bug_index: string, file_path: string, code_snippet: string)
4. extract_method_code: This command allows you to extract possible implementations of a given method name inside a file. The required params to call this command are: (project_name: string, bug_index: integer, filepath: string, method_name: string)\n"""

        query += self.construct_bug_report_context()

        if self.read_files != {}:
            query += self.construct_read_files_context()

        query += "Project name: " + self.project_name + "\n"
        query += "Bug index: " + self.bug_index + "\n"
        query += """let me add a description of how you express a command call:
This is the format:
```ts
interface Response {
name: string;
args: Record<string, any>;
}
```
Here is an example:
{
"name": "run_tests",
"args": {
"name": "Chart",
"index": 1
}
Write all the commands calls using this format (ignore the command used in the example, its just to illustrate)

please use the indicated format and produce a list, like this:
[
    {"name":..., "args":...},
    {"name":..., "args":...},
    ...
    {"name":..., "args":...}
]"""
        try:
            self.suggested_commands = json.loads(query_for_commands(query))
        except Exception as e:
            logger.info("EXCEPTION HAPPENED IN COMMANDS SUGGESTION-*-*-*-*-*-*-*-*-*-*-*-*-*-\n\n")

        for cmd in self.suggested_commands:
            name, args = extract_command(cmd, None, self.config)
            exec_result = execute_command(name, args)
            if name == "search_code_base":
                self.pre_search += "Searching keywords: {}, returned the following results:\n{}\n\n".format(str(args), exec_result)
            if name == "extract_method_code":
                self.pre_methods_code +=  str(exec_result) + "\n"
            if name == "get_classes_and_methods":
                self.pre_search += "\nExtracted methods and classes from {} and the result is the following:\n {}".format(args, exec_result)
            if name == "extract_similar_functions_calls":
                self.pre_similar += "Search query {} found the following similar functions calls:\n{}\n\n".format(str(args), exec_result)

    def load_context(self,):
        #with open("experimental_setups/experiments_list.txt") as eht:
        #    exps = eht.read().splitlines()
        exps = self.exps
        with open(os.path.join("experimental_setups", exps[-1], "saved_contexts", "saved_context_{}_{}".format(self.project_name, self.bug_index)), "r") as patf:
            context = json.load(patf)

        self.cycle_budget = context["cycle_budget"]
        self.cycle_count = context["cycle_count"]
        self.cycles_remaining = context["cycle_remaining"]
        self.current_state = context["current_state"]
        self.prompt_dictionary = context["prompt_dictionary"]
        self.project_name = context["project_name"]
        self.bug_index = context["bug_index"]
        self.localization_info = context["localization_info"]
        self.tests_results = context["test_results"]
        self.read_files = context["read_files"]
        self.suggested_fixes = context["suggested_fixes"]
        self.search_queries = context["search_queries"]
        self.bug_report = context["bug_report"]
        self.commands_history = context["commands_history"]
        self.human_feedback = context["human_feedback"]
        self.ask_chatgpt = context["ask_chatgpt"]
        self.hypothesises = context["hypothesises"]
        self.initial_bug_report = context["initial_bug_report"]
        self.buggy_lines = context["buggy_lines"]
        self.similar_calls = context["similar_calls"]
        self.extracted_methods = context["extracted_methods"]
        self.experiment_file = context["experiment_file"]
        self.hyperparams = context["hyperparams"]
        self.history = context["history"]
        
    def construct_fix_query(self,):
        
        hypothesis_string = self.construct_hypothesises_context()
        read_files_section = self.construct_read_files_context()
        suggested_fixes_section = self.construct_fixes_context()
        search_queries = self.construct_search_context()
        bug_report = self.construct_bug_report_context()
        similar_calls_context = self.construct_similar_calls_context()

        prelude = "This is the info we gathered so far about the bug. Unfortunately, we cannot gather any more info. You have to suggested a fixed based the following given information and ofcourse based on your knowledge."
        context_prompt = prelude + "\n" + bug_report + "\n" + "\n" + read_files_section + "\n" + suggested_fixes_section + "\n" + search_queries + "\n" +\
            similar_calls_context + "\n".join(self.prompt_dictionary["fix format"]) + "\n\n"
        
        context_prompt += "Task: Suggest a list of 10 possible fixes, output a list in the following form: [fix1, fix2, ..., fix10]\n"
        
        return context_prompt

    def validate_command_parsing(self, command_dict):
        with open("commands_interface.json") as cif:
            commands_interface = json.load(cif)

        command_dict = command_dict.get("command", {"name": "", "args": {}})
        if command_dict["name"] in list(commands_interface.keys()):
            ref_args = commands_interface[command_dict["name"]]
            if isinstance(command_dict["args"], dict):
                command_args = list(command_dict["args"].keys())
                if set(command_args) == set(ref_args):
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False
        
    def detect_command_repetition(self, ref_cmd):
        #with open("assistant_output_from_command_repetition.json", "w") as aocr:
        #    json.dump(assistant_outputs+[str(ref_cmd["command"])], aocr)
        try:
            assistant_outputs = [str(extract_dict_from_response(msg.content)["command"]) for msg in self.history if msg.role == "assistant"]
            if str(ref_cmd["command"]) in assistant_outputs:
                logger.info("WARNING: REPETITION DETECTED!\n\n")
                return True
            else:
                return False
        except Exception as e:
            with open("exception_files.txt", "w") as ef:
                ef.write(str(e))
            print("Exception raised,", e)
            return False
        
    def handle_command_repitition(self, repeated_command: dict, handling_strategy: str = ""):
        if handling_strategy == "":
            return ""
        elif handling_strategy == "RESTRICT":
            return "Your next command should be totally different from this command: {}".format(repeated_command["command"])
        elif handling_strategy == "TOP3":
            return "Suggest three commands that would make sense to execute given your current input. Give the full json object of each command with all attributes, put the three commands in a list, i.e, [{...}, {...}, {...}]. Do not add any text explanataion before or after the list of the three commands."
        else:
            raise ValueError("The value given to the param handling_strategy is unsuported: {}".format(handling_strategy))
        
    def construct_read_files(self, command_name = "read_range"):
        skip_next = False
        read_files = {}
        messages_history = [msg for _, msg in enumerate(self.history)]
        read_result = None
        # check command dict
        for i in range(len(messages_history)):
            if skip_next:
                skip_next = False
                continue
            skip_next = False
            msg = messages_history[i]
            if msg.role == "assistant":
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] == command_name:
                    lines_range=(
                        command_dict["command"]["args"]["startline"],
                        command_dict["command"]["args"]["endline"])
                    file_path = command_dict["command"]["args"]["filepath"]
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        read_result = next_msg.content
                        skip_next= True
                    if read_result:
                        if file_path in read_files:
                            read_files[file_path][lines_range] = read_result
                        else:
                            read_files[file_path] = {
                                lines_range: read_result
                            }
                    else:
                        skip_next = False
                else:
                    skip_next = False
        self.read_files = read_files

    def construct_generated_methods(self, command_name = "AI_generate_method_code"):
        skip_next = False
        messages_history = [msg for _, msg in enumerate(self.history)]
        gen_result = None
        # check command dict
        for i in range(len(messages_history)):
            if skip_next:
                skip_next = False
                continue
            skip_next = False
            msg = messages_history[i]
            if msg.role == "assistant":
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] == command_name:
                    method_name = command_dict["command"]["args"]["method_name"]
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        gen_result = next_msg.content
                        skip_next= True
                    if gen_result:
                        self.generated_methods = (method_name, gen_result)
                    else:
                        skip_next = False
                else:
                    skip_next = False

    def construct_commands_history(self):
        messages_history = [msg for _, msg in enumerate(self.history)]
        commands_history = []
        for i in range(len(messages_history)):
            msg = messages_history[i]
            if msg.role == "assistant" and not msg.content.startswith("## As RepairAgentv0.5.0, this is the last command I have called in response to the users' input"):
                command_dict = extract_dict_from_response(msg.content)
                try:
                    commands_history.append(command_dict["command"]["name"] + " , Your reasoning for calling this command was: '{}'".format(
                            command_dict["thoughts"]
                        )
                    )
                except:
                    pass
        self.commands_history = commands_history

    def construct_suggested_fixes(self, command_names = ["write_range", "write_fix", "try_fixes"]):
        skip_next = False
        suggested_fixes = []
        messages_history = [msg for _, msg in enumerate(self.history)]
        for i in range(len(messages_history)):
            if skip_next:
                continue
            skip_next = False
            msg = messages_history[i]
            if msg.role == "assistant":
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] in command_names:
                    if command_dict["command"]["name"] in ["write_range", "write_fix"]:
                        changes_dicts = command_dict["command"]["args"].get("changes_dicts", [])
                        suggested_fixes.append(changes_dicts)
                    else:
                        for f in command_dict["command"]["args"]["fixes_list"]:
                            changes_dicts = f["changes_dicts"]
                            suggested_fixes.append(changes_dicts)

        self.suggested_fixes = suggested_fixes
 
    def construct_human_feedback(self):
        human_feedback = []
        messages_history = [msg for _, msg in enumerate(self.history)]
        for i in range(len(messages_history)):
            msg = messages_history[i]
            if msg.role == "system":
                if msg.content.startswith("Human feedback"):
                    human_feedback.append(msg.content)
        self.human_feedback = human_feedback

    def construct_unknown_commands(self,):
        skip_next = False
        unknown_commands = []
        messages_history = [msg for _, msg in enumerate(self.history)]
        for i in range(len(messages_history)):
            if skip_next:
                continue
            skip_next = False
            msg = messages_history[i]
            if msg.role == "assistant" and not msg.content.startswith("## As RepairAgentv0.5.0, this is the last command I have called in response to the users' input"):
                try:
                    command_dict = extract_dict_from_response(msg.content)
                    command_name = command_dict["command"]["name"]
                    
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        if next_msg.role == "user":
                            if "unknown command. Do not try to use this command again." in next_msg.content:
                                if command_name not in unknown_commands:
                                    unknown_commands.append(command_name)
                except:
                    pass
        return unknown_commands
    
    def construct_search_queries(self, command_name="search_code_base"):
        skip_next = False
        search_queries = []
        search_result = None
        messages_history = [msg for _, msg in enumerate(self.history)]
        for i in range(len(messages_history)):
            if skip_next:
                skip_next = False
                continue
            skip_next = False
            msg = messages_history[i]
            if msg.role == "assistant" and not msg.content.startswith("## As RepairAgentv0.5.0, this is the last command I have called in response to the users' input"):
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] == command_name:
                    key_words = command_dict["command"]["args"]["key_words"]
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        search_result = next_msg.content
                        skip_next= True
                    if search_result:
                        search_queries.append({
                            "query": key_words,
                            "result": search_result
                        })
        self.search_queries = search_queries

    def construct_similar_calls(self, command_name="extract_similar_functions_calls"):
        skip_next = False
        search_queries = []
        search_result = None
        messages_history = [msg for _, msg in enumerate(self.history)]
        for i in range(len(messages_history)):
            if skip_next:
                skip_next = False
                continue
            skip_next = False
            msg = messages_history[i]
            if msg.role == "assistant" :
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] == command_name:
                    code_snippet = command_dict["command"]["args"]["code_snippet"]
                    file_path = command_dict["command"]["args"]["file_path"]
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        search_result = next_msg.content
                        skip_next= True
                    if search_result:
                        search_queries.append({
                            "code_snippet": code_snippet,
                            "file_path": file_path,
                            "result": search_result
                        })
        self.similar_calls = search_queries

    def construct_extracted_methods(self, command_name="extract_method_code"):
        skip_next = False
        search_queries = []
        search_result = None
        messages_history = [msg for _, msg in enumerate(self.history)]
        for i in range(len(messages_history)):
            if skip_next:
                skip_next = False
                continue
            skip_next = False
            msg = messages_history[i]
            if msg.role == "assistant" :
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] == command_name:
                    method_name = command_dict["command"]["args"]["method_name"]
                    file_path = command_dict["command"]["args"]["filepath"]
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        search_result = next_msg.content
                        skip_next= True
                    if search_result:
                        search_queries.append({
                            "method_name": method_name,
                            "file_path": file_path,
                            "result": search_result
                        })
        self.extracted_methods = search_queries

    def construct_bug_report(self):
        messages_history = [msg for _, msg in enumerate(self.history)]
        """
        for i in range(len(messages_history)):
            msg = messages_history[i]
            if msg.role == "assistant" and not msg.content.startswith("## As RepairAgentv0.5.0, this is the last command I have called in response to the users' input"):
                command_dict = extract_dict_from_response(msg.content)
                if command_dict["command"]["name"] == "get_info":
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        get_info = next_msg.content
                        self.prompt_dictionary["commands"][2].replace("2. get_info: Gets info about a specific bug in a specific project, params: (name: string, index: integer). This command can only be executed once\n", "")
                        break
        """
        """
        for i in range(len(messages_history)):
            msg = messages_history[i]
            if msg.role == "assistant" and not msg.content.startswith("## As RepairAgentv0.5.0, this is the last command I have called in response to the users' input"):
                command_dict = extract_dict_from_response(msg.content)
                if command_dict["command"]["name"] == "run_tests":
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        run_tests = next_msg.content
                        self.prompt_dictionary["commands"][2].replace("3. run_tests: Runs the test cases of the project being analyzed, params: (name: string, index: integer). This command can only be executed once.\n", "")
                        break
        """
        failing_test_code = ""
        for i in range(len(messages_history)):
            msg = messages_history[i]    
            if msg.role == "assistant" and not msg.content.startswith("## As RepairAgentv0.5.0, this is the last command I have called in response to the users' input"):
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] == "extract_test_code":
                    if i < len(messages_history) - 1:
                        j = i + 1
                        next_msg = messages_history[j]
                        failing_test_code += "Extracting test code from file {} returned: ".format(command_dict["command"]["args"]["test_file_path"]) + next_msg.content + "\n"

        if get_info or run_tests or failing_test_code:
            self.bug_report = {"get_info": "No longer needed for this version", "run_tests": "No longer needed for this version", "failing_test_code": failing_test_code}


    def construct_hypothesises(self,):
        self.hypothesises = []
        messages_history = [msg for _, msg in enumerate(self.history)]
        for i in range(len(messages_history)):
            msg = messages_history[i]
            if msg.role == "assistant" and not msg.content.startswith("## As RepairAgentv0.5.0, this is the last command I have called in response to the users' input"):
                command_dict = extract_dict_from_response(msg.content)
                if not self.validate_command_parsing(command_dict):
                    continue
                if command_dict["command"]["name"] == "express_hypothesis":
                    self.hypothesises.append(command_dict["command"]["args"]["hypothesis"])
    
    def update_prompt_state(self, state_name):
        """
        Given a state name, this function would update the prompt dictionary to include the right description of the state 
        and also the corresponding set of commands.
        """
        self.prompt_dictionary["current state"] = self.descriptions[state_name]
        self.prompt_dictionary["commands"][2] = self.cmds_by_state[state_name]
        self.current_state = state_name

    def switch_state(self):
        """
        check whether the last executed command causes a state change.
        If so, update the prompt based on the changed state
        """
        
        for i in range(len(self.history)-1, 0, -1):
            if self.history[i].role == "assistant":
                if "Hypothesis discarded! You are now back at the state 'collect information to understand the bug'" in self.history[i+1].content:
                    if self.current_state != "collect information to understand the bug":
                        self.update_prompt_state("collect information to understand the bug")
                elif "You are now back at the state 'collect information to fix the bug'" in self.history[i+1].content:
                    if self.current_state != "collect information to fix the bug":
                        self.update_prompt_state("collect information to fix the bug")
                elif "Since you have a hypothesis about the bug, the current state have been changed from 'collect information to understand the bug' to 'collect information to fix the bug'" in self.history[i+1].content:
                    if self.current_state != "collect information to fix the bug":
                        self.update_prompt_state("collect information to fix the bug")
                elif "\n **Note:** You are automatically switched to the state 'trying out candidate fixes'" in self.history[i+1].content:
                    if self.current_state != "trying out candidate fixes":
                        self.update_prompt_state("trying out candidate fixes")
                break

    def construct_hypothesises_context(self,):
        hypothesis_string = "## Hypothesis about the bug:\n"
        if self.hypothesises:
            for h in self.hypothesises[:-1]:
                hypothesis_string += "- (Refuted) " + h + "\n"

            hypothesis_string += "- (Current hypothesis) " + self.hypothesises[-1] + "\n"
        else:
            hypothesis_string += "No hypothesis made yet.\n"

        return hypothesis_string
    

    def construct_read_files_context(self,):
        read_files_section = "## Read lines:\n"
        if self.read_files:
            for f in self.read_files:
                for r in self.read_files[f]:
                    read_files_section += "Lines {} to {} from file: {}\n{}\n\n".format(r[0], r[1], f, self.read_files[f][r])
        else:
            read_files_section+="No files have been read so far.\n"

        return read_files_section
    
    def construct_fixes_context(self,):
        suggested_fixes_section = "## Suggested fixes:\n"+"This is the list of suggested fixes so far but none of them worked:\n"
        if self.suggested_fixes:
            for f in self.suggested_fixes:
                suggested_fixes_section += "###Fix:\n{}\n\n".format(str(f))
        else:
            suggested_fixes_section += "No fixes were suggested yet.\n"
        return suggested_fixes_section
    
    def construct_search_context(self,):
        search_queries = "## Executed search queries within the code base:\n"
        if self.search_queries:
            for s in self.search_queries:
                search_queries += "Searching keywords: {}, returned the following results:\n{}\n\n".format(s["query"], s["result"])
        else:
            search_queries += "No search queries executed so far.\n"
        return search_queries
    
    def construct_extracted_methods_context(self,):
        extracted_methods = "## The list of emplementations of some methods in the code base:\n"
        if self.extracted_methods:
            for s in self.extracted_methods:
                extracted_methods += s["result"] + "\n"
        else:
            extracted_methods += "No extracted methods so far.\n"
        return extracted_methods
    
    def construct_similar_calls_context(self,):
        search_queries = "## Functions calls extracted based on snippets of code and target files:\n"
        if self.similar_calls:
            for s in self.similar_calls:
                search_queries += "Code snippet: {}\ntarget file: {}\nsimilar functions calls that were found:\n{}\n\n".format(s["code_snippet"], s["file_path"],s["result"])
        else:
            search_queries += "No similar functions  calls were extracted.\n"
        return search_queries

    def construct_bug_report_context(self,):
        bug_report = "## Info about the bug (bug report summary):\n"

        if self.bug_report:
            bug_report += "### Bug info:\n"+ self.localization_info.replace("#FAULT_OF_OMISSION", "") + "\n" +\
            "### Test cases results:\n"+ self.tests_results +"\n" +\
            ("### The code of the failing test cases:\n" if self.bug_report["failing_test_code"] else "")+ self.bug_report["failing_test_code"]+"\n"
        else:
            bug_report += "No info was collected about the bug so far. You can get more info about the bug by running the commands: get_info and run_tests.\n"
        return bug_report
    
    def construct_commands_history_context(self,):
        commands_history = "## The list of commands you have executed so far:\n"
        if self.commands_history:
            commands_history += "\n".join(self.commands_history)
        return commands_history
    
    def construct_human_feedback_context(self,):
        human_feedback = "## The list of human feedbacks:\n"
        if self.human_feedback:
            human_feedback += "\n".join(self.human_feedback)
        human_feedback += "\n"
        return human_feedback
    
    def construct_generated_methods_context(self,):
        generated_methods = "## AI generated regeneration of buggy method:\n"
        if self.generated_methods:
            generated_methods += "\n".join("The regeneration of method {} has returned".format(self.generated_methods[0], self.generated_methods[1]))
        generated_methods += "No AI generated code yet.\n"
        return generated_methods
    
    def construct_context_prompt(self,):
        
        context_prompt = "What follows are sections of the most important information you gathered so far about the current bug.\
        Use the following info to suggest a fix for the buggy code:\n"
        
        hypothesis_string = self.construct_hypothesises_context()
        read_files_section = self.construct_read_files_context()
        suggested_fixes_section = self.construct_fixes_context()
        search_queries = self.construct_search_context()
        bug_report = self.construct_bug_report_context()
        commands_history = self.construct_commands_history_context()
        similar_calls_context = self.construct_similar_calls_context()
        extracted_methods_context = self.construct_extracted_methods_context()
        generated_methods = self.construct_generated_methods_context()

        unknow_cmd = "## DO NOT TRY TO USE THE FOLLOWING COMMANDS IN YOUR NEXT ACTION (NEVER AT ALL):\n" + "\n".join(self.construct_unknown_commands())

        context_prompt += bug_report + "\n" + hypothesis_string + "\n" + read_files_section + "\n" + generated_methods +"\n"+ extracted_methods_context + "\n" + suggested_fixes_section + "\n" + search_queries + "\n" +\
            similar_calls_context + "\n" + unknow_cmd + \
            "\n" + "**Important:** This is the end of information sections. After this, you will see the last command you executed (if you executed any so far) and the result of its execution. Continue your reasoning from there.\n"

        return context_prompt

    def construct_mutation_prompt(self, last_patch, detailed_buggies):
        hypothesis_string = self.construct_hypothesises_context()
        read_files_section = self.construct_read_files_context()
        suggested_fixes_section = self.construct_fixes_context()
        search_queries = self.construct_search_context()
        bug_report = self.construct_bug_report_context()
        commands_history = self.construct_commands_history_context()
        similar_calls_context = self.construct_similar_calls_context()
        extracted_methods_context = self.construct_extracted_methods_context()
        fix_template = create_fix_template(self.project_name, self.bug_index)
        info_sections = []
        if "No info was collected about the bug so far. You can get more info about the bug by running the commands: get_info and run_tests.\n" not in bug_report:
            info_sections.append(bug_report)

        if "No files have been read so far.\n" not in read_files_section:
            info_sections.append(read_files_section)

        if "No fixes were suggested yet.\n" not in suggested_fixes_section:
            info_sections.append(suggested_fixes_section)

        if "No extracted methods so far.\n" not in extracted_methods_context:
            info_sections.append(extracted_methods_context)

        if "No similar functions  calls were extracted.\n" not in similar_calls_context:
            info_sections.append(similar_calls_context)

        if "No search queries executed so far.\n" not in search_queries:
            info_sections.append(search_queries)

        context_prompt = "What follows are sections of the most important information that we have gathered so far about the bug.\
        Make usage of the following information to suggest mutations of fixes:\n"

        context_prompt += "\n".join(info_sections)
        context_prompt += "\n" + "\n".join(self.prompt_dictionary["fix format"])
        #context_prompt += "\n" + "For reference, here is a patch that you can start mutating from (if not available create your own):\n" + str(last_patch) +"\n\n"
        with open("hints.txt") as htt:
            hints = htt.read()

        list_example = '[{"file_name": "org/apache/commons/codec/binary/Base64.java", "insertions": [], "deletions": [], "modifications": [{"line_number": 225, "modified_line": "        this(true);"}]}, {"file_name": "org/apache/commons/codec/binary/Base64.java", "insertions": [], "deletions": [], "modifications": [{"line_number": 225, "modified_line": "        this(null);"}]}, {"file_name": "org/apache/commons/codec/binary/Base64.java", "insertions": [], "deletions": [], "modifications": [{"line_number": 225, "modified_line": "        this(1==0);"}]}, {"file_name": "org/apache/commons/codec/binary/Base64.java", "insertions": [], "deletions": [], "modifications": [{"line_number": 225, "modified_line": "        this(1 - 2);"}]}, ...]'
        context_prompt += "Here are some hints that might help you in suggesting good mutations:\n" + hints + "\n\n"
        context_prompt += detailed_buggies
        context_prompt += "Task for assistant:  generate 30 mutants of the target buggy lines. Respect the fix format, only change values (never touch keys). For every mutant generate a full fix dictionary. Put the 30 mutants in a main list."
        # For example: {}. Make sure your output is json parsable.".format(list_example)

        context_prompt += "To generate the list of your mutations, fillout the following template multiple time with different variants:\n"
        context_prompt += fix_template + "\n"
        return context_prompt

    def save_to_json(self, path, json_content, mode="a"):
        if not os.path.exists(path):
            
            if isinstance(json_content, list):
                with open(path, "w") as json_file:
                    json.dump(json_content, json_file)
                return json_content
            elif isinstance(json_content, dict):
                file_content = []
                new_contents = []
                if any(x in [k.lower() for k in json_content.keys()] for x in ["mutants", "mutants list", "mutants_list", "possible_mutants", "possible_mutants", "mutations", "possible mutations", "possible_mutations", "mutations_list", "mutations list", "fixes", "possible fixes", "possible_fixes", "fixes list", "fixes_list"]):
                    for _, v in json_content.items():
                        file_content.extend(v)
                        new_contents.extend(v)
                else:
                    file_content.append(json_content)
                    new_contents.append(json_content)
                with open(path, "w") as json_file:
                    json.dump(file_content, json_file)

                return new_contents
        else:
            with open(path) as json_file:
                file_content: list = json.load(json_file)

            if isinstance(json_content, list):
                file_content.extend(json_content)
                with open(path, "w") as json_file:
                    json.dump(file_content, json_file)
                return json_content
            
            elif isinstance(json_content, dict):
                new_contents = []
                if any(x in [k.lower() for k in json_content.keys()] for x in ["mutants", "mutants list", "mutants_list", "possible_mutants", "possible_mutants", "mutations", "possible mutations", "possible_mutations", "mutations_list", "mutations list", "fixes", "possible fixes", "possible_fixes", "fixes list", "fixes_list"]):
                    for _, v in json_content.items():
                        file_content.extend(v)
                        new_contents.extend(v)
                else:
                    file_content.append(json_content)
                    new_contents.append(json_content)

                with open(path, "w") as json_file:
                    json.dump(file_content, json_file)

                return new_contents

    def think(
        self,
        instruction: Optional[str] = None,
        thought_process_id: ThoughtProcessID = "one-shot",
    ) -> tuple[CommandName | None, CommandArgs | None, AgentThoughts]:
        """Runs the agent for one cycle.

        Params:
            instruction: The instruction to put at the end of the prompt.

        Returns:
            The command name and arguments, if any, and the agent's thoughts.
        """

        instruction = instruction or self.default_cycle_instruction

        prompt: ChatSequence = self.construct_prompt(instruction, thought_process_id)
        prompt = self.on_before_think(prompt, thought_process_id, instruction)
        
        ## This is a line added by me to save prompts at each step
        prompt_text = prompt.dump()
        start_i = prompt_text.find("bug within the project")
        end_i = prompt_text.find(".\n2.")
        in_between = prompt_text[start_i:end_i]
        project_name, bug_index= in_between.replace("bug within the project ", "").replace(' and bug index ', " ").replace('"', "").split(" ")[:2]

        exps = self.exps
        with open(os.path.join("experimental_setups", exps[-1], "logs", "prompt_history_{}_{}".format(project_name, bug_index)), "a+") as patf:
            patf.write(prompt.dump())
        
        # handle querying strategy
        # For now, we do not evaluate the external query
        # we just want to observe how good is it
        if self.hyperparams["external_fix_strategy"] != 0:
            if self.cycle_count % self.hyperparams["external_fix_strategy"] == 0:
                query = self.construct_fix_query()
                suggested_fixes = query_for_fix(query, )
                self.save_to_json(os.path.join("experimental_setups", exps[-1], "external_fixes", "external_fixes_{}_{}.json".format(project_name, bug_index)), json.loads(suggested_fixes))

        raw_response = create_chat_completion(
            prompt,
            self.config,
            functions=get_openai_command_specs(self.command_registry)
            if self.config.openai_functions
            else None,
        )
        
        try:
            response_dict = extract_dict_from_response(
                raw_response.content
            )
            repetition = self.detect_command_repetition(response_dict)
            if repetition:
                logger.info("WARNING: REPETITION DETECTED!\n")
                logger.info(str(self.handle_command_repitition(response_dict, self.hyperparams["repetition_handling"])) + "\n\n")
                prompt.extend([Message("user", self.handle_command_repitition(response_dict, self.hyperparams["repetition_handling"]))])
                new_response = create_chat_completion(
                        prompt,
                        self.config,
                        functions=get_openai_command_specs(self.command_registry)
                        if self.config.openai_functions
                        else None,
                    )
                if self.hyperparams["repetition_handling"] == "TOP3":
                    top3_list = json.loads(new_response.content)
                    for r in top3_list:
                        repetition = self.detect_command_repetition(r)
                        if not repetition:
                            raw_response = Message("assistant", str(r))
                elif self.hyperparams["repetition_handling"] == "RESTRICT":
                    raw_response = new_response
            self.cycle_count += 1

            return self.on_response(raw_response, thought_process_id, prompt, instruction)
        except SyntaxError as e:
            return self.on_response(raw_response, thought_process_id, prompt, instruction)
        
    @abstractmethod
    def execute(
        self,
        command_name: str | None,
        command_args: dict[str, str] | None,
        user_input: str | None,
    ) -> str:
        """Executes the given command, if any, and returns the agent's response.

        Params:
            command_name: The name of the command to execute, if any.
            command_args: The arguments to pass to the command, if any.
            user_input: The user's input, if any.

        Returns:
            The results of the command.
        """
        ...

    def construct_base_prompt(
        self,
        thought_process_id: ThoughtProcessID,
        prepend_messages: list[Message] = [],
        append_messages: list[Message] = [],
        reserve_tokens: int = 0,
    ) -> ChatSequence:
        """Constructs and returns a prompt with the following structure:
        1. System prompt
        2. `prepend_messages`
        3. Message history of the agent, truncated & prepended with running summary as needed
        4. `append_messages`

        Params:
            prepend_messages: Messages to insert between the system prompt and message history
            append_messages: Messages to insert after the message history
            reserve_tokens: Number of tokens to reserve for content that is added later
        """

        ## added this part to change the prompt structure
        if len(self.history) >= 2:
            self.switch_state()

        self.construct_read_files()
        self.construct_suggested_fixes()
        self.construct_search_queries()
        self.construct_bug_report()
        self.construct_commands_history()
        self.construct_human_feedback()
        self.construct_hypothesises()
        self.construct_similar_calls()
        self.construct_extracted_methods()
        self.save_context()

        with open("cycle_instruction_text.txt") as cit:
            cycle_instruction = cit.read()

        if self.hyperparams["budget_control"]["name"] == "NO-TRACK":
            pass
        elif self.hyperparams["budget_control"]["name"] == "FULL-TRACK" and self.hyperparams["budget_control"]["params"]=={}:
            cycle_instruction += "\nYou have, so far, executed {} commands, you have only {} commands left.\n".format(self.cycle_count, self.hyperparams["commands_limit"]-self.cycle_count)
        elif self.hyperparams["budget_control"]["name"] == "FULL-TRACK" and self.hyperparams["budget_control"]["params"]!={}:
            n_fixes = self.hyperparams["budget_control"]["params"]["#fixes"]
            cycle_instruction += "\nYou have, so far, executed, {} commands and suggested {} fixes. You have {} commands left. However, you need to suggest {} fixes before consuming all the left commands.\n".format(self.cycle_count, len(self.suggested_fixes), self.hyperparams["commands_limit"]-self.cycle_count, n_fixes - len(self.suggested_fixes))
        elif self.hyperparams["budget_control"]["name"]=="FORCED":
            t1 = self.hyperparams["budget_control"]["T1"]
            t2 = self.hyperparams["budget_control"]["T2"]
            if self.cycle_count >= t2:
                self.update_prompt_state("trying out candidate fixes")
                cycle_instruction += "\nBecause of budget constaints, you were forced to transition to the state 'trying out candidate fixes'" 
            elif self.cycle_count >= t1:
                self.update_prompt_state("collect information to fix the bug")
                cycle_instruction += "\nBecause of budget constaints, you were forced to transition to the state 'collect information to fix the bug'" 

        context_prompt = self.construct_context_prompt()
        prompt = ChatSequence.for_model(
            self.llm.name,
            [Message("system", self.prompt_dictionary["role"])])
        
        definitions_prompt = ""
        static_sections_names = ["goals", "current state", "commands", "general guidelines"]
        if self.current_state in ["collect information to fix the bug", "trying out candidate fixes"]:
            static_sections_names.append("fix format")
        for key in static_sections_names:
            if isinstance(self.prompt_dictionary[key], list):
                definitions_prompt += "\n".join(self.prompt_dictionary[key]) + "\n"
            elif isinstance(self.prompt_dictionary[key], str):
                definitions_prompt += self.prompt_dictionary[key] + "\n"
            else:
                raise TypeError("For now we only support list and str types.")
            
        prompt.extend(ChatSequence.for_model(
            self.llm.name,
            [Message("user", definitions_prompt + "\n" + context_prompt + "\n\n" + cycle_instruction)] + prepend_messages,
        ))
        #prompt.append(Message("user", context_prompt))
        
        ## The following is the original code, uncomment when needed to roll back
        """
       # Reserve tokens for messages to be appended later, if any
        reserve_tokens += self.history.max_summary_tlength
        if append_messages:
            reserve_tokens += count_message_tokens(append_messages, self.llm.name)

        # Fill message history, up to a margin of reserved_tokens.
        # Trim remaining historical messages and add them to the running summary.
        history_start_index = len(prompt)
        trimmed_history = add_history_upto_token_limit(
            prompt, self.history, self.send_token_limit - reserve_tokens
        )
        
        if trimmed_history:
            new_summary_msg, _ = self.history.trim_messages(list(prompt), self.config)
            prompt.insert(history_start_index, new_summary_msg)

        """
        if len(self.history) > 2:
            last_command = self.history[-2]
            command_result = self.history[-1]
            last_command_section = "{}\n".format(last_command.content)
            append_messages.append(Message("assistant", last_command_section))
            result_last_command = "The result of executing that last command is:\n {}".format(command_result.content)
            append_messages.append((Message("user", result_last_command)))
        if append_messages:
            prompt.extend(append_messages)

        return prompt

    def construct_prompt(
        self,
        cycle_instruction: str,
        thought_process_id: ThoughtProcessID,
    ) -> ChatSequence:
        """Constructs and returns a prompt with the following structure:
        1. System prompt
        2. Message history of the agent, truncated & prepended with running summary as needed
        3. `cycle_instruction`

        Params:
            cycle_instruction: The final instruction for a thinking cycle
        """

        if not cycle_instruction:
            raise ValueError("No instruction given")

        #cycle_instruction_msg = Message("user", cycle_instruction)
        cycle_instruction_tlength = 0
        #count_message_tokens(
        #    cycle_instruction_msg, self.llm.name
        #)

        append_messages: list[Message] = []

        response_format_instr = self.response_format_instruction(thought_process_id)
        #if response_format_instr:
        #s    append_messages.append(Message("user", response_format_instr))

        prompt = self.construct_base_prompt(
            thought_process_id,
            append_messages=append_messages,
            reserve_tokens=cycle_instruction_tlength,
        )

        # ADD user input message ("triggering prompt")
        #prompt.append(cycle_instruction_msg)

        return prompt

    # This can be expanded to support multiple types of (inter)actions within an agent
    def response_format_instruction(self, thought_process_id: ThoughtProcessID) -> str:
        if thought_process_id != "one-shot":
            raise NotImplementedError(f"Unknown thought process '{thought_process_id}'")

        RESPONSE_FORMAT_WITH_COMMAND = """```ts
        interface Response {
            // Express your thoughts based on the information that you have collected so far, the possible steps that you could do next and also your reasoning about fixing the bug in question"
            thoughts: string;
            command: {
                name: string;
                args: Record<string, any>;
            };
        }
        ```
        Here is an example of command call that you can output:
        {
            "thoughts": "I have information about the bug, but I need to run the test cases to understand the bug better.",
            "command": {
                "name": "run_tests",
                "args": {
                "name": "Chart",
                "index": 1
                }
            }
        }
        """

        RESPONSE_FORMAT_WITHOUT_COMMAND = """```ts
        interface Response {
            thoughts: {
                // Thoughts
                text: string;
                reasoning: string;
                // Short markdown-style bullet list that conveys the long-term plan
                plan: string;
                // Constructive self-criticism
                criticism: string;
                // Summary of thoughts to say to the user
                speak: string;
            };
        }
        ```"""

        response_format = re.sub(
            r"\n\s+",
            "\n",
            RESPONSE_FORMAT_WITHOUT_COMMAND
            if self.config.openai_functions
            else RESPONSE_FORMAT_WITH_COMMAND,
        )

        use_functions = self.config.openai_functions and self.command_registry.commands
        return (
            f"Respond strictly with JSON{', and also specify a command to use through a function_call' if use_functions else ''}. "
            "The JSON should be compatible with the TypeScript type `Response` from the following:\n"
            f"{response_format}\n"
        )

    def on_before_think(
        self,
        prompt: ChatSequence,
        thought_process_id: ThoughtProcessID,
        instruction: str,
    ) -> ChatSequence:
        """Called after constructing the prompt but before executing it.

        Calls the `on_planning` hook of any enabled and capable plugins, adding their
        output to the prompt.

        Params:
            instruction: The instruction for the current cycle, also used in constructing the prompt

        Returns:
            The prompt to execute
        """
        current_tokens_used = prompt.token_length
        plugin_count = len(self.config.plugins)
        for i, plugin in enumerate(self.config.plugins):
            if not plugin.can_handle_on_planning():
                continue
            plugin_response = plugin.on_planning(
                self.ai_config.prompt_generator, prompt.raw()
            )
            if not plugin_response or plugin_response == "":
                continue
            message_to_add = Message("system", plugin_response)
            tokens_to_add = count_message_tokens(message_to_add, self.llm.name)
            if current_tokens_used + tokens_to_add > self.send_token_limit:
                logger.debug(f"Plugin response too long, skipping: {plugin_response}")
                logger.debug(f"Plugins remaining at stop: {plugin_count - i}")
                break
            prompt.insert(
                -1, message_to_add
            )  # HACK: assumes cycle instruction to be at the end
            current_tokens_used += tokens_to_add
        return prompt

    def on_response(
        self,
        llm_response: ChatModelResponse,
        thought_process_id: ThoughtProcessID,
        prompt: ChatSequence,
        instruction: str,
    ) -> tuple[CommandName | None, CommandArgs | None, AgentThoughts]:
        """Called upon receiving a response from the chat model.

        Adds the last/newest message in the prompt and the response to `history`,
        and calls `self.parse_and_process_response()` to do the rest.

        Params:
            llm_response: The raw response from the chat model
            prompt: The prompt that was executed
            instruction: The instruction for the current cycle, also used in constructing the prompt

        Returns:
            The parsed command name and command args, if any, and the agent thoughts.
        """

        # Save assistant reply to message history
        self.history.append(prompt[-1])
        self.history.add(
            "assistant", llm_response.content, "ai_response"
        )  # FIXME: support function calls

        try:
            return self.parse_and_process_response(
                llm_response, thought_process_id, prompt, instruction
            )
        except SyntaxError as e:
            logger.error(f"Response could not be parsed: {e}")
            with open("parsing_erros_responses.txt", "a") as pers:
                pers.write(llm_response.content+"\n")
            # TODO: tune this message
            self.history.add(
                "system",
                f"Your response could not be parsed."
                "\n\nRemember to only respond using the specified format above!",
            )
            return None, None, {}

        # TODO: update memory/context

    @abstractmethod
    def parse_and_process_response(
        self,
        llm_response: ChatModelResponse,
        thought_process_id: ThoughtProcessID,
        prompt: ChatSequence,
        instruction: str,
    ) -> tuple[CommandName | None, CommandArgs | None, AgentThoughts]:
        """Validate, parse & process the LLM's response.

        Must be implemented by derivative classes: no base implementation is provided,
        since the implementation depends on the role of the derivative Agent.

        Params:
            llm_response: The raw response from the chat model
            prompt: The prompt that was executed
            instruction: The instruction for the current cycle, also used in constructing the prompt

        Returns:
            The parsed command name and command args, if any, and the agent thoughts.
        """
        pass


def add_history_upto_token_limit(
    prompt: ChatSequence, history: MessageHistory, t_limit: int
) -> list[Message]:
    current_prompt_length = prompt.token_length
    insertion_index = len(prompt)
    limit_reached = False
    trimmed_messages: list[Message] = []
    for cycle in reversed(list(history.per_cycle())):
        messages_to_add = [msg for msg in cycle if msg is not None]
        tokens_to_add = count_message_tokens(messages_to_add, prompt.model.name)
        if current_prompt_length + tokens_to_add > t_limit:
            limit_reached = True

        if not limit_reached:
            # Add the most recent message to the start of the chain,
            #  after the system prompts.
            prompt.insert(insertion_index, *messages_to_add)
            current_prompt_length += tokens_to_add
        else:
            trimmed_messages = messages_to_add + trimmed_messages

    return trimmed_messages