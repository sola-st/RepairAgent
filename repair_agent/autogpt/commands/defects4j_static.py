import os
import subprocess
from pathlib import Path
import re
import json
from autogpt.logs import logger


STATIC_MODEL = "gpt-4o-mini"

def get_info(name: str, index: int, workspace) -> str:
    """Create and execute a Python file in a Docker container and return the STDOUT of the
    executed code. If there is any data that needs to be captured use a print statement

    Args:
        name (str): Project name
        index (str): Bug number

    Returns:
        str: The info about the bug given by defects4j framework
    """

    return execute_get_info(name, index, workspace)

def execute_get_info(name: str, index:int, workspace):
    cmd_temp = "defects4j info -p {} -b {}"
    cmd = cmd_temp.format(name, index)

    """Gets info about a specific bug of a project

    Args:
        name (str): The name of the project
        index (int): The index number of the target bug
        agent (Agent): The agent piloting the execution 
    Returns:
        str: The output of the info command
    """
    logger.info(
        f"Getting info for project '{name}', bug number {index}, in working directory '{workspace}'"
    )

    if we_are_running_in_a_docker_container():
        logger.debug(
            f"Auto-GPT is running in a Docker container..."
        )
        result = subprocess.run(
            [cmd],
            capture_output=True,
            encoding="utf8",
            cwd=workspace,
            shell=True
        )
        if result.returncode == 0:
            root_cause = extract_root_cause(result.stdout)
            edited_files = get_edited_files(name, index)
            localization_info = get_localization(name, index)
            return root_cause + "\n"+ localization_info
        else:
            return f"Error: {result.stderr}"
    else:
        logger.debug("Auto-GPT is not running in a Docker container")
        return "Tricky situation! Auto-GPT is not running in a Docker container"
    
    # TODO("Adapt this code later to run inside docker if it's not already running")

def run_tests(name: str, index: int, workspace) -> str:
    """Create and execute a Python file in a Docker container and return the STDOUT of the
    executed code. If there is any data that needs to be captured use a print statement

    Args:
        code (str): The Python code to run
        name (str): A name to be given to the Python file

    Returns:
        str: The STDOUT captured from the code when it ran
    """

    return run_defects4j_tests(name, index, workspace)

def run_defects4j_tests(name: str, index:int, workspace):
    cmd_temp = "cd {} && defects4j compile && defects4j test"
    folder_name = "_".join([name.lower(), str(index), "buggy"])
    cmd = cmd_temp.format(folder_name)

    """Run tests on a given project and a bug number

    Args:
        name (str): The name of the project for which we want to execute the test suite
        index (int): The number of the target bug (the test cases would trigger that bug)
    Returns:
        str: The output of executing the test suite
    """
    logger.info(
        f"Executing test suite for project '{name}', bug number {index}"
    )

    if we_are_running_in_a_docker_container():
        logger.debug(
            f"Auto-GPT is running in a Docker container; executing tests directly..."
        )
        result = subprocess.run(
            [cmd],
            capture_output=True,
            encoding="utf8",
            cwd=workspace,
            shell=True
        )
        if result.returncode == 0:
            logger.debug(
                "NO ERROR IF: " +result.stdout)
            if "BUILD FAILED" in result.stdout:
                with open(os.path.join(workspace, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write("")
                undo_c = run_checkout(name, index, workspace)
                return result.stdout[result.stdout.find("BUILD FAILED"):]
            else:
                with open(os.path.join(workspace, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write(result.stdout)
                fail_report = extract_fail_report(name, index, workspace)
                undo_c = run_checkout(name, index, workspace)
                return fail_report
        else:
            if "BUILD FAILED" in result.stderr:
                with open(os.path.join(workspace, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write("")
                undo_c = run_checkout(name, index, workspace)
                return result.stderr[result.stderr.find("BUILD FAILED"):]
            else:
                with open(os.path.join(workspace, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write("")
                undo_c = run_checkout(name, index, workspace)
                return result.stderr
    else:
        logger.debug("Auto-GPT is not running in a Docker container")
        return "Tricky situation! Auto-GPT is not running in a Docker container"
    
    # TODO("Adapt this code later to run inside docker if it's not already running")

def run_checkout(name: str, index:int, workspace):
    cmd_temp = "defects4j checkout -p {} -v {}b -w {}"
    folder_name = "_".join([name.lower(), str(index), "buggy"])
    if os.path.exists(os.path.join("auto_gpt_workspace", folder_name)):
        os.system("rm -rf {}".format(os.path.join("auto_gpt_workspace", folder_name)))
    cmd = cmd_temp.format(name, index, folder_name)

    """Undo the changes that you made to the project and restore the original content of all files

    Args:
        name (str): The name of the project
        index (int): The number of the target bug
        agent (Agent): The agent piloting the execution 
    Returns:
        str: The output of the checkout command
    """
    logger.info(
        f"Restoring project '{name}', bug number {index}, in working directory '{workspace}'"
    )

    if we_are_running_in_a_docker_container():
        logger.debug(
            f"Auto-GPT is running in a Docker container; executing tests directly..."
        )
        result = subprocess.run(
            [cmd],
            capture_output=True,
            encoding="utf8",
            cwd=workspace,
            shell=True
        )
        if result.returncode == 0:
            return "The changed files were restored to their original content"
        else:
            return f"Error: {result.stderr}"
    else:
        logger.debug("Auto-GPT is not running in a Docker container")
        return "Tricky situation! Auto-GPT is not running in a Docker container"

def we_are_running_in_a_docker_container() -> bool:
    """Check if we are running in a Docker container

    Returns:
        bool: True if we are running in a Docker container, False otherwise
    """
    return True
    return os.path.exists("/.dockerenv")

def extract_root_cause(info):
    separator = "--------------------------------------------------------------------------------"
    start_cause = info.find("Root cause")
    end_cause = info[start_cause:].find(separator)
    root_cause = info[start_cause:start_cause+end_cause]
    return root_cause


def extract_failing_test(output_message):
    # Define a regular expression pattern to match failing test information
    pattern = re.compile(r'Failing tests: (\d+)\n\s+- (.+::\w+)')
    
    # Search for the pattern in the output message
    match = pattern.search(output_message)
    
    if match:
        # Extract the number of failing tests and the test case information
        num_failures = int(match.group(1))
        test_case_info = match.group(2)
        
        # Split the test case information into class and function
        class_name, function_name = test_case_info.split('::')
        
        return {
            'num_failures': num_failures,
            'class_name': class_name,
            'function_name': function_name
        }
    else:
        return None

def get_edited_files(name, index):
    target_file = "defects4j/framework/projects/{name}/patches/{index}.src.patch".format(name=name, index=index)
    with open(target_file) as ptf:
        diff_content = ptf.readlines()

    files_list = []
    for line in diff_content:
        if line.startswith("diff --git"):
            files_list.append(extract_file_name(line))
    return files_list


def extract_lines_range(name, index):
    import whatthepatch
    target_file = "defects4j/framework/projects/{name}/patches/{index}.src.patch".format(name=name, index=index)
    with open(target_file) as ptf:
        text = ptf.readlines()
    diff = [x for x in whatthepatch.parse_patch(text)]
    min_max = []
    for diff0 in diff:
        max = 0
        min = 99999999999999
        for d in diff0.changes:
            if d.new is not None:
                if d.new < min:
                    min = d.new
                if d.new > max:
                    max = d.new
        min_max.append((min, max-5))
    return min_max

def get_localization(name, index):
    localization_dir = "defects4j/buggy-lines"
    methods_dir = "defects4j/buggy-methods"
    file_name = "{}-{}.buggy.lines".format(name, index)
    if not os.path.exists(os.path.join(localization_dir, file_name)):
        lines_info = ""
    else:
        with open(os.path.join(localization_dir, file_name)) as buggy_lines_file:
            bug_lines = buggy_lines_file.read()

        # better use the format of detailed buggy lines
        lines_info = "The bug is located at exactly these lines numbers: (the format is file-name#line-number# line-code):\n" + bug_lines

    file_name = "{}-{}.buggy.methods".format(name, index)

    if not os.path.exists(os.path.join(methods_dir, file_name)):
        methods_info = ""
    else:

        methods_info = "The following is the list of buggy methods:\n"
        with open(os.path.join(methods_dir, file_name)) as methods:
            methods_list = methods.read().splitlines()

        print(methods_info)
        for m in methods_list:
            if m.endswith("1"):
                methods_info += m +'\n'
    return lines_info + "\n" + methods_info

def get_list_of_buggy_lines(name, index):
    localization_dir = "defects4j/buggy-lines"
    methods_dir = "defects4j/buggy-methods"
    file_name = "{}-{}.buggy.lines".format(name, index)
    if not os.path.exists(os.path.join(localization_dir, file_name)):
        return []
    else:
        with open(os.path.join(localization_dir, file_name)) as buggy_lines_file:
            bug_lines = buggy_lines_file.read().splitlines()
        lines = []
        for bl in bug_lines:
            lines.append(bl.split("#")[-2])
        return lines

def extract_file_name(diff_line):
    diff_line = diff_line.split(" ")
    return "/".join(diff_line[2].split("/")[1:])

def extract_fail_report(name: str, index: str, workspace):
    project_dir = "{}_{}_buggy".format(name.lower(), index)
    workspace = workspace

    with open(os.path.join(workspace, project_dir, "failing_tests")) as wp_file:
        fail_content = wp_file.read().splitlines()

    failing_test_cases = []
    current_case = []
    case_base = ""
    for line in fail_content:
        if line.startswith("---"):
            if current_case:
                failing_test_cases.append(current_case)
                current_case = []
                case_base = ""
            current_case.append(line)
            case_base = line[4:line.find("::") if "::" in line else 1/0]
            ".".join(case_base.split(".")[:-1])
        elif line.startswith("\tat "):
            if case_base in line:
                current_case.append(line)
        else:
            current_case.append(line)

    if current_case:
        failing_test_cases.append(current_case)

    logger.debug(str(failing_test_cases))
    
    return "There are {} failing test cases, here is the full log of failing cases:\n".format(len(failing_test_cases))+\
        "\n\n".join(["\n".join(ftc) for ftc in failing_test_cases])

from langchain.chat_models import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage, AIMessage

def query_for_fix(query, model=STATIC_MODEL):
    chat = ChatOpenAI(openai_api_key="API-KEY-PLACEHOLDER", model=model)

    messages = [
        SystemMessage(
            content="You are an automated program repair agent who suggests fixes to given bugs." +\
                    "Particularly, you will be given some information about a bug." +\
                    "Your task is to suggest a list of possible fixes for the given bug. Usually, the given information contains an approximate location of the bug. Respect the fix format described below. Output a json parsable output enclosed in a list."
                    ),
        HumanMessage(
            content=query
            )  
    ]
    response = chat.invoke(messages)

    return response.content

def query_for_mutants(query, model=STATIC_MODEL):
    chat = ChatOpenAI(openai_api_key="API-KEY-PLACEHOLDER", model=model)

    messages = [
        SystemMessage(
            content="You are a code assitant and program repair agent who suggests fixes to given bugs." +\
                    "Particularly, you will be given some information about a bug." +\
                    "Your task is to suggest a list of possible mutations of the buggy code. Probably mutating it a little bit would fix the bug."+\
                    "Use the information that I give you and also your general knowledge of similar code snippets or bug fixes that you know of."+\
                    "Respect the fix format, described below, for every mutant that you generate."
                    ),
        HumanMessage(
            content=query
            )  
    ]
    #response_format={ "type": "json_object" }
    response = chat.invoke(messages)

    return response.content


def construct_fix_command(fix_object, project_name, bug_index):
    if isinstance(fix_object, dict):
        fix_object = [fix_object]
    elif isinstance(fix_object, list):
        pass
    elif isinstance(fix_object, str):
        try:
            fix_object = json.loads(fix_object)
            if isinstance(fix_object, dict):
                fix_object = [fix_object]
        except Exception as e:
            return str(e)

    return {
            "thoughts": "executing the mutants",
            "command":{
                "name": "write_fix",
                "args":{
                    "project_name":project_name,
                    "bug_index":bug_index,
                    "changes_dicts": fix_object
                }
            }
        }


def query_for_commands(query, model=STATIC_MODEL):
    chat = ChatOpenAI(openai_api_key="API-KEY-PLACEHOLDER", model=model)

    messages = [
        SystemMessage(
            content="I have a set of functions that help me analyze and repair buggy code. I will give you the description of the functions (I also call them commands), and the buggy piece of code and tell me what commands would make sense to call to get more info about the bug."
                    ),
        HumanMessage(
            content=query
            )  
    ]
    #response_format={ "type": "json_object" }
    response = chat.invoke(messages)

    return response.content

def list_java_files(main_dir) -> list:
    directory = main_dir
    java_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".java"):
                java_files.append(os.path.join(root.replace("{}/".format(main_dir), ""), file))

    return java_files

from antlr4 import FileStream, CommonTokenStream
from JavaLexer import JavaLexer
from JavaParser import JavaParser
from JavaListener import JavaListener
from antlr4 import ParseTreeWalker

class FunctionExtractor(JavaListener):
    def __init__(self):
        self.matched_methods = []
        self.target_name = ""

    def enterMethodDeclaration(self, ctx):
        method_name = ctx.Identifier().getText()
        method_body = ctx.methodBody().getText()
        method_params = ctx.formalParameters().getText()
        if method_name == self.target_name:
            self.matched_methods.append((method_name, method_body, method_params))

def extract_method_code(project_name, bug_index, method_name, file_path):
    workspace = "./auto_gpt_workspace"
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
    if filepath.endswith(".java"):
        filepath = filepath[:-5]
        filepath.replace(".", "/")
        filepath += ".java"
    else:
        filepath = filepath.replace(".", "/")
    
    if not os.path.exists(os.path.join(workspace, project_dir, filepath)):
        if not os.path.exists(os.path.join(workspace, project_dir, "files_index.txt")):
            with open(os.path.join(workspace, project_dir, "files_index.txt"), "w") as fit:
                fit.write("\n".join(list_java_files(os.path.join(workspace, project_dir))))
                
        with open(os.path.join(workspace, project_dir, "files_index.txt")) as fit:
            files_index = [f for f in fit.read().splitlines() if filepath in f]

        if len(files_index) == 1:
            filepath = files_index[0]
        elif len(files_index) >= 1:
            raise ValueError("Multiple Candidate Paths. We do not handle this yet!")
        else:
            return "The filepath {} does not exist.".format(filepath)
    
    input_stream = FileStream(os.path.join(workspace, project_dir, filepath))
    
    lexer = JavaLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = JavaParser(token_stream)
    
    tree = parser.compilationUnit()
    
    extractor = FunctionExtractor()
    extractor.target_name = method_name
    walker = ParseTreeWalker()
    walker.walk(extractor, tree)
    return [b[1] for i, b in enumerate(extractor.matched_methods)]
    
import tiktoken
def extract_function_def_context(project_name, bug_index, method_name, file_path):
    input_limit = 12000
    extracted_methods = extract_method_code(project_name, bug_index, method_name, file_path)
    if len(extract_method_code) == 0:
        raise ValueError("NO EXTRACTED METHODS, SHOULD NOT HAPPEN")
    method_body = extracted_methods[0]
    workspace = "./auto_gpt_workspace"
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
    with open(os.path.join(workspace, project_dir, file_path)) as wpf:
        file_content = wpf.read()

    start_index = file_content.find(method_body)
    if start_index == -1:
        raise ValueError("METHOD BODY NOT FOUD, INDEX = -1, SHOULD NOT HAPPEN")
    context = file_content[:start_index]
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    encoded_context = enc.encode(context)
    if len(encoded_context) < input_limit:
        return context
    else:
        return enc.decode(context[-input_limit:])
    
def auto_complete_functions(project_name, bug_index, file_path, method_name, model=STATIC_MODEL):
    context = extract_function_def_context(project_name, bug_index, method_name, file_path)
    chat = ChatOpenAI(openai_api_key="API-KEY-PLACEHOLDER", model=model)
    messages = [
            SystemMessage(
                content="implement the code for the method {}, here is the code before the method:".format(method_name)),
            HumanMessage(
                content=context
                )  
        ]
        #response_format={ "type": "json_object" }
    response = chat.invoke(messages)
    return response.content

def extract_command(
    assistant_reply_json: dict, assistant_reply, config
) -> tuple[str, dict[str, str]]:
    """Parse the response and return the command name and arguments

    Args:
        assistant_reply_json (dict): The response object from the AI
        assistant_reply (ChatModelResponse): The model response from the AI
        config (Config): The config object

    Returns:
        tuple: The command name and arguments

    Raises:
        json.decoder.JSONDecodeError: If the response is not valid JSON

        Exception: If any other error occurs
    """
    if config.openai_functions:
        if assistant_reply.function_call is None:
            return "Error:", {"message": "No 'function_call' in assistant reply"}
        assistant_reply_json["command"] = {
            "name": assistant_reply.function_call.name,
            "args": json.loads(assistant_reply.function_call.arguments),
        }
    try:
        if "command" not in assistant_reply_json:
            return "Error:", {"message": "Missing 'command' object in JSON"}

        if not isinstance(assistant_reply_json, dict):
            return (
                "Error:",
                {
                    "message": f"The previous message sent was not a dictionary {assistant_reply_json}"
                },
            )

        command = assistant_reply_json["command"]
        if not isinstance(command, dict):
            return "Error:", {"message": "'command' object is not a dictionary"}

        if "name" not in command:
            return "Error:", {"message": "Missing 'name' field in 'command' object"}

        command_name = command["name"]

        # Use an empty dictionary if 'args' field is not present in 'command' object
        arguments = command.get("args", {})

        return command_name, arguments
    except json.decoder.JSONDecodeError:
        return "Error:", {"message": "Invalid JSON"}
    # All other errors, return "Error: + error message"
    except Exception as e:
        return "Error:", {"message": str(e)}


def execute_command(
    command_name: str,
    arguments: dict[str, str],
    agent,
):
    """Execute the command and return the result

    Args:
        command_name (str): The name of the command to execute
        arguments (dict): The arguments for the command
        agent (Agent): The agent that is executing the command

    Returns:
        str: The result of the command
    """
    try:
        # Execute a native command with the same name or alias, if it exists
        if command := agent.command_registry.get_command(command_name):
            return command(**arguments, agent=agent)

        # Handle non-native commands (e.g. from plugins)
        for command in agent.ai_config.prompt_generator.commands:
            if (
                command_name == command.label.lower()
                or command_name == command.name.lower()
            ):
                return command.function(**arguments)

        raise RuntimeError(
            f"Cannot execute '{command_name}': unknown command."
            " Do not try to use this command again."
        )
    except Exception as e:
        return f"Error: {str(e)}"

def get_detailed_list_of_buggy_lines(name, index):
    localization_dir = "defects4j/buggy-lines"
    methods_dir = "defects4j/buggy-methods"
    file_name = "{}-{}.buggy.lines".format(name, index)
    if not os.path.exists(os.path.join(localization_dir, file_name)):
        return []
    else:
        with open(os.path.join(localization_dir, file_name)) as buggy_lines_file:
            bug_lines = buggy_lines_file.read().splitlines()
        lines = []
        for bl in bug_lines:
            if bl.replace("\n", "").replace(" ", "").replace("\t", "") == "":
                continue
            lines.append((int(bl.split("#")[1]), bl.split("#")[0]))
        
        ret_val = "Your fix should target all the following lines by at least one edit type (modification, insertion, or deletion):\n"
        for l in lines:
            ret_val += str(l[0]) + " from file: " + l[1] + "\n"

        ret_val += "\n"
        return ret_val

def parse_buggy_lines(buggy_lines):
	parsed_lines = {}
	for line in buggy_lines:
		splitted_line = line.split("#")
		if splitted_line[0] in parsed_lines:
			parsed_lines[splitted_line[0]].append((splitted_line[1], splitted_line[2]))
		else:
			parsed_lines[splitted_line[0]] = [(splitted_line[1], splitted_line[2])]
	return parsed_lines


def create_fix_template(project_name, bug_number):
	with open("defects4j/buggy-lines/{}-{}.buggy.lines".format(project_name, bug_number)) as bgl:
		buggy_lines = bgl.read().splitlines()
	parsed_lines = parse_buggy_lines(buggy_lines)
	
	fix_template = []
	for key in parsed_lines:
		new_dict = {
        "file_name": key,
		"target_lines": parsed_lines[key],
        "insertions": [],
        "deletions": [],
        "modifications": []
    	}
		fix_template.append(new_dict)

	fix_template_str = json.dumps(fix_template)
	fix_template_str = fix_template_str.replace('"modifications": []', '"modifications": [here put the list of modification dictionaries {"line_number":..., "modified_line":...}, ...]')
	fix_template_str = fix_template_str.replace('"deletions": []', '"deletions": [here put the lines number to delete...]')
	fix_template_str = fix_template_str.replace('"insertions": []', '"insertions": [here put the list of insertion dictionaries. DO NOT REPEAT ALREADY EXISTING LINES!: {"line_numbe":..., "new_lines":[...]}, ...]')
	return fix_template_str

if __name__ =="__main__":
    file_path = "src/com/google/javascript/jscomp/NodeUtil.java"
    method_name = "mayBeString"
    project_name = "Closure"
    bug_index = "10"
    print(auto_complete_functions(project_name, bug_index, file_path, method_name))