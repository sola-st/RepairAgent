

class PromptParser():

    def __init__(self, prompt_text):
        self.role = ""
        self.state = ""
        self.goals = ""
        self.general_guidelines = ""
        self.commands = ""
        self.simple_bugs_patterns = ""
        self.hypothesis = ""
        self.read_lines = ""
        self.suggested_fixes = ""
        self.search_queries = ""
        self.info = {
            "get_info": "",
            "run_tests": "",
            "extract_test_code": ""
        }

        self.commands_list = []
        self.prompt_text = prompt_text

    def parse_prompt_text_legacy(self):
        start_goals = self.prompt_text.find("## Goals")
        if start_goals == -1:
            raise ValueError("Goals section should always be in the prompt")
        self.role = self.prompt_text[:start_goals]
        
        start_state = self.prompt_text.find("## Current state")
        if start_state == -1:
            raise ValueError("Current state should always be in the prompt")
        self.goals = self.prompt_text[start_goals: start_state]

        start_commands = self.prompt_text.find("## Commands")
        if start_commands == -1:
            raise ValueError("List of commands should always be in the prompt")
        self.state = self.prompt_text[start_state: start_commands]

        start_guidlines = self.prompt_text.find("## General guidelines")
        if start_guidlines == -1:
            raise ValueError("Guidelines should always be in the prompt")
        self.commands = self.prompt_text[start_commands: start_guidlines]

        start_patterns = self.prompt_text.find("## Simple Bugs patterns")
        if start_patterns == -1:
            raise ValueError("Bugs patterns should be in the prompt")
        self.general_guidelines = self.prompt_text[start_guidlines:start_patterns]

        start_hypothesis = self.prompt_text.find("## Hypothesis about the bug")
        if start_hypothesis == -1:
            raise ValueError("Hypothesis should be in the prompt")
        self.simple_bugs_patterns = self.prompt_text[start_patterns:start_hypothesis]

        start_read_lines = self.prompt_text.find("## Read lines")
        if start_read_lines == -1:
            raise ValueError("Read lines section should be in the prompt")
        self.hypothesis = self.prompt_text[start_hypothesis:start_read_lines]

        start_fixes = self.prompt_text.find("## Suggested fixes")
        if start_fixes == -1:
            raise ValueError("Suggested fixes section should be in the prompt")
        self.read_lines = self.prompt_text[start_read_lines:start_fixes]

        start_search_queries = self.prompt_text.find("## Executed search queries within the code base")
        if start_search_queries == -1:
            raise ValueError("Search queries section should be in the prompt")
        self.suggested_fixes = self.prompt_text[start_fixes:start_search_queries]

        start_info = self.prompt_text.find("## Info about the bug (bug report summary)")
        if start_info == -1:
            raise ValueError("Info summary should always be in the prompt")
        self.search_queries = self.prompt_text[start_search_queries:start_info]

        start_commands_list = self.prompt_text.find("## The list of commands you have executed so far")
        if start_commands_list == -1:
            raise ValueError("Commands list section should be in the prompt")
        self.info = self.parse_info_section(self.prompt_text[start_info: start_commands_list])


        end_sections = self.prompt_text.find("## DO NOT TRY TO USE THE FOLLOWING COMMANDS IN YOUR NEXT ACTION (NEVER AT ALL):")
        self.commands_list = self.prompt_text[start_commands_list:end_sections]

    def parse_info_section(self, info_text):
        bug_info = ""
        test_cases = ""
        test_code = ""
        start_bug_info = info_text.find("### Bug info:")
        start_test_cases = info_text.find("### Test cases results:")
        start_test_code = info_text.find("### The code of the failing test cases:")
        if start_bug_info != -1:
            if start_test_cases !=-1:
                bug_info = info_text[start_bug_info:start_test_cases]
            elif start_test_code != -1:
                bug_info = info_text[start_bug_info:start_test_code]
            else:
                bug_info = info_text[start_bug_info:]

        if start_test_cases != -1:
            if start_test_code != -1:
                test_cases = info_text[start_test_cases:start_test_code]
            else:
                test_cases = info_text[start_test_cases:]

        if start_test_code != -1:
            test_code = info_text[start_test_code]

        return {
            "get_info": bug_info,
            "run_tests": test_cases,
            "extract_test_code": test_code
        }