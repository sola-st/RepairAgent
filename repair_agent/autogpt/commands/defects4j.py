"""Commands to execute code"""

COMMAND_CATEGORY = "defects4j"
COMMAND_CATEGORY_TITLE = "Run Tests"

import os
import shutil
import subprocess
import re
import json
import random
import time

from autogpt.agents.agent import Agent
from autogpt.command_decorator import command
from autogpt.logs import logger

import javalang
from create_files_index import list_java_files

ALLOWLIST_CONTROL = "allowlist"
DENYLIST_CONTROL = "denylist"

def preprocess_paths(agent, project_name, bug_index, filepath):
    workspace = agent.config.workspace_path
    project_dir = os.path.join(workspace, project_name.lower()+"_"+str(bug_index)+"_buggy")
    
    if filepath.endswith(".java"):
        filepath = filepath[:-5]
        filepath = filepath.replace(".", "/")
        filepath += ".java"
    else:
        filepath = filepath.replace(".", "/")
    
    if not os.path.exists(os.path.join(project_dir,filepath)):
        if not os.path.exists(os.path.join(project_dir, "files_index.txt")):
            with open(os.path.join(project_dir, "files_index.txt"), "w") as fit:
                fit.write("\n".join(list_java_files(project_dir)))
            
        with open(os.path.join(project_dir, "files_index.txt")) as fit:
            files_index = [f for f in fit.read().splitlines() if filepath in f]
        
        if len(files_index) == 1:
            filepath = files_index[0]
        elif len(files_index) >= 1:
            raise ValueError("Multiple Candidate Paths. We do not handle this yet!")
        else:
            return "The filepath {} does not exist.".format(filepath)
    return filepath

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
    fix_template_str = fix_template_str.replace('"modifications": []', '"modifications": [] #here put the list of modification dictionaries{"line_number":..., "modified_line":...}, ...')
    fix_template_str = fix_template_str.replace('"deletions": []', '"deletions": [] #here put the lines number to delete...')
    fix_template_str = fix_template_str.replace('"insertions": []', '"insertions": [] #here put the list of insertion dictionaries targeting the lines marked with FAULT_OF_OMISSON: {"line_numbe":..., "new_lines":[...]}, ...')
    return fix_template_str

def create_deletion_template(project_name, bug_number):
    with open("defects4j/buggy-lines/{}-{}.buggy.lines".format(project_name, bug_number)) as bgl:
        buggy_lines = bgl.read().splitlines()
    parsed_lines = parse_buggy_lines(buggy_lines)
    if "FAULT_OF_OMISSION" in str(parsed_lines):
        return None
    fix_template = []
    for key in parsed_lines:
        new_dict = {
        "file_name": key,
        "insertions": [],
        "deletions": [t[0] for t in parsed_lines[key]],
        "modifications": []
    	}
        fix_template.append(new_dict)
    return fix_template


def run_checkout(project_name: str, bug_index:int, agent: Agent):
    cmd_temp = "defects4j checkout -p {} -v {}b -w {}"
    folder_name = "_".join([project_name.lower(), str(bug_index), "buggy"])
    workspace_dir = os.path.join("auto_gpt_workspace", folder_name)
    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)
    cmd = cmd_temp.format(project_name, bug_index, folder_name)

    """Undo the changes that you made to the project and restore the original content of all files

    Args:
        project_name (str): The name of the project
        bug_index (int): The number of the target bug
        agent (Agent): The agent piloting the execution 
    Returns:
        str: The output of the checkout command
    """
    logger.info(
        f"Restoring project '{project_name}', bug number {bug_index}, in working directory '{agent.config.workspace_path}'"
    )

    if we_are_running_in_a_docker_container():
        logger.debug(
            f"Auto-GPT is running in a Docker container; executing tests directly..."
        )
        result = subprocess.run(
            [cmd],
            capture_output=True,
            encoding="utf8",
            cwd=agent.config.workspace_path,
            shell=True
        )
        if result.returncode == 0:
            return "The changed files were restored to their original content"
        else:
            return f"Error: {result.stderr}"
    else:
        logger.debug("Auto-GPT is not running in a Docker container")
        return "Tricky situation! Auto-GPT is not running in a Docker container"

def undo_changes(project_name: str, bug_index: int, agent: Agent) -> str:
    """Undo the changes that you made to the project and restore the original content of all files

    Args:
        project_name (str): Project name
        bug_index (int): The index of the bug

    Returns:
        str: A success message or a failure message depending on the exit code
    """
    return run_checkout(project_name, bug_index, agent)

@command(
    "run_tests",
    "Runs the test cases of the project being analyzed. This command can only be used for one time",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project for which the test cases should be run.",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you are trying to fix.",
            "required": True

        }
    },
)
def run_tests(project_name: str, bug_index: int, agent: Agent) -> str:
    """Create and execute a Python file in a Docker container and return the STDOUT of the
    executed code. If there is any data that needs to be captured use a print statement

    Args:
        

    Returns:
        str: The STDOUT captured from the code when it ran
    """
    return run_defects4j_tests(project_name, bug_index, agent)

def run_defects4j_tests(project_name: str, bug_index:int, agent: Agent):
    cmd_temp = "cd {} && defects4j compile && defects4j test"
    folder_name = "_".join([project_name.lower(), str(bug_index), "buggy"])
    cmd = cmd_temp.format(folder_name)

    """Run tests on a given project and a bug number

    Args:
        name (str): The name of the project for which we want to execute the test suite
        index (int): The number of the target bug (the test cases would trigger that bug)
    Returns:
        str: The output of executing the test suite
    """
    logger.info(
        f"Executing test suite for project '{project_name}', bug number {bug_index}"
    )

    if we_are_running_in_a_docker_container():
        logger.debug(
            f"Auto-GPT is running in a Docker container; executing tests directly..."
        )
        result = subprocess.run(
            [cmd],
            capture_output=True,
            encoding="utf8",
            cwd=agent.config.workspace_path,
            shell=True
        )
        if result.returncode == 0:
            logger.debug(
                "NO ERROR IF: " +result.stdout)
            if "BUILD FAILED" in result.stdout:
                with open(os.path.join(agent.config.workspace_path, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write("")
                undo_changes(project_name, bug_index, agent)
                return result.stdout[result.stdout.find("BUILD FAILED"):]
            else:
                with open(os.path.join(agent.config.workspace_path, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write(result.stdout)
                fail_report = extract_fail_report(project_name, bug_index, agent)
                undo_changes(project_name, bug_index, agent)
                return fail_report
        else:
            if "BUILD FAILED" in result.stderr:
                with open(os.path.join(agent.config.workspace_path, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write("")
                undo_changes(project_name, bug_index, agent)
                return result.stderr[result.stderr.find("BUILD FAILED"):]
            else:
                with open(os.path.join(agent.config.workspace_path, folder_name+"_test.txt"), "w") as testrf:
                    testrf.write("")
                undo_changes(project_name, bug_index, agent)
                return result.stderr
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



@command(
    "get_info",
    "Gets info about a specific bug in a specific project. This command should be executed only once meaning that if the command was executed before according to the history of commands, you should not call it again.",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project.",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you want to get info about.",
            "required": True

        }
    },
)
def get_info(project_name: str, bug_index: int, agent: Agent) -> str:
    """Create and execute a Python file in a Docker container and return the STDOUT of the
    executed code. If there is any data that needs to be captured use a print statement

    Args:
        name (str): Project name
        index (str): Bug number

    Returns:
        str: The info about the bug given by defects4j framework
    """
    return execute_get_info(project_name, bug_index, agent)

def execute_get_info(project_name: str, bug_index:int, agent: Agent):
    cmd_temp = "defects4j info -p {} -b {}"
    cmd = cmd_temp.format(project_name, bug_index)

    """Gets info about a specific bug of a project

    Args:
        name (str): The name of the project
        index (int): The index number of the target bug
        agent (Agent): The agent piloting the execution 
    Returns:
        str: The output of the info command
    """
    logger.info(
        f"Getting info for project '{project_name}', bug number {bug_index}, in working directory '{agent.config.workspace_path}'"
    )

    if we_are_running_in_a_docker_container():
        logger.debug(
            f"Auto-GPT is running in a Docker container..."
        )
        result = subprocess.run(
            [cmd],
            capture_output=True,
            encoding="utf8",
            cwd=agent.config.workspace_path,
            shell=True
        )
        if result.returncode == 0:
            root_cause = extract_root_cause(result.stdout)
            edited_files = get_edited_files(project_name, bug_index)
            lines_range = extract_lines_range(project_name, bug_index)
            ## need to include hunks numbers
            localization_info = get_localization(project_name, bug_index)
            return root_cause + "\n"+ localization_info
        
            #"Buggy files and range of possible buggy line numbers:\n" +\
            #"\n".join(["In file: {}  ,lines from {} to {}".format(ef, *lr) for ef, lr in zip(edited_files, lines_range)]) 
        else:
            return f"Error: {result.stderr}"
    else:
        logger.debug("Auto-GPT is not running in a Docker container")
        return "Tricky situation! Auto-GPT is not running in a Docker container"

@command(
    "read_range",
    "Read a range of lines in a given file",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project.",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you want to get info about.",
            "required": True

        },
        "filepath": {
            "type": "string",
            "description": "The path to the file to read from.",
            "required": True,
        },
        "startline":{
            "type": "integer",
            "description": "The number of the line to start reading from in the given file.",
            "required": True

        },
        "endline":{
            "type": "integer",
            "description": "The number of the line to stop reading at.",
            "required": True

        }
    },
)
def read_range(project_name:str, bug_index:int, filepath: str, startline: int, endline:int, agent: Agent) -> str:
    """Read a range of lines starting from line number startline and ending at line number endline

    Args:
        name (str): The name of the project
        index (int): The index number of the target bug
        filename (str): The path to the file to read from
        startline (int): The line number at which the reading starts
        endline (int): The line number at which the reading ends

    Returns:
        str: The read lines between startline and endline
    """
    return execute_read_range(project_name, bug_index, filepath, startline, endline, agent)

@command(
    "try_fixes",
    """This is a very useful command when you want to try multiple fixes quickly. This function allows you to try a list of fixes, the function will execute related tests to see if any of the fixes work.
    The list that you pass this function should be of the form:
    fixes_list: [{"project_name":"project name", "bug_index":"bug index", "filepath":"path to file to edit", "changed_lines":{"162": "new code here ..."}}, {...}, ...]""",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project.",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you want to get info about.",
            "required": True

        },
        "fixes_list":  {
            "type": "dict",
            "description": "The list of fixes to try.",
            "required": True,
        },
    },
)
def try_fixes(project_name: str, bug_index:int, fixes_list, agent: Agent):
    fixes_feedback = ""
    successful_ones = []
    if len(fixes_list) == 0:
        return "The list of fixes you gave is empty. Please try again with a non empty list of fixes."
    elif isinstance(fixes_list[0], dict):
        write_result = execute_write_range(project_name, bug_index, fixes_list, agent)
        if "0 failing test cases" in write_result:
            successful_ones.append(0)
        fixes_feedback += "Fix 0: " + write_result + "\n"

        return "In summary, we applied all your fixes and {} of them passed. The indexes of the ones that passed are {}.\
          Here are more details:\n".format(len(successful_ones), successful_ones) +\
        fixes_feedback
    for i, fix in enumerate(fixes_list):
        write_result = execute_write_range(project_name, bug_index, fix, agent)
        if "0 failing test cases" in write_result:
            successful_ones.append(i)
        fixes_feedback += "Fix {}: ".format(i) + write_result + "\n"

    return "In summary, we applied all your fixes and {} of them passed. The indexes of the ones that passed are {}.\
          Here are more details:\n".format(len(successful_ones), successful_ones) +\
        fixes_feedback

@command(
    "write_range",
    "Write a list of lines into a file, the parameter changed_lines is a dictionary that contains lines numbers as keys and the new content of that line as value (only include changed lines). The test cases are run automatically after running the changes. The changes are reverted automatically if the the test cases fail.",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project.",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you want to get info about.",
            "required": True

        },
        "filepath": {
            "type": "string",
            "description": "The path to the file to write to",
            "required": True,
        },
        "changed_lines":{
            "type": "dict",
            "description": "a dictionary of the changed lines",
            "required": True

        }
    },
)
def write_range(project_name:str, bug_index:int, changes_dicts: list, agent: Agent) -> str:
    """Write a list of lines into a file to replace all lines between startline and endline

    Args:
        name (str): The name of the project
        index (int): The index number of the target bug
        filename (str): The path to the file to write to
        startline (int): The number of the line at which the replacement starts
        endline (int): The number of the line at which the replacement stops
        lines_list list[string]: The list of the new lines to be written to the file

    Returns:
        str: Success message or error message if it was not successful
    """
    return execute_write_range(project_name, bug_index, changes_dicts, agent)


@command(
    "write_fix",
    "Write a list of lines into a file, the parameter changed_lines is a dictionary that contains lines numbers as keys and the new content of that line as value (only include changed lines). The test cases are run automatically after running the changes. The changes are reverted automatically if the the test cases fail.",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project.",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you want to get info about.",
            "required": True

        },
        "filepath": {
            "type": "string",
            "description": "The path to the file to write to",
            "required": True,
        },
        "changed_lines":{
            "type": "dict",
            "description": "a dictionary of the changed lines",
            "required": True

        }
    },
)
def write_fix(project_name:str, bug_index:int, changes_dicts: list, agent: Agent) -> str:
    """Write a list of lines into a file to replace all lines between startline and endline

    Args:
        name (str): The name of the project
        index (int): The index number of the target bug
        filename (str): The path to the file to write to
        startline (int): The number of the line at which the replacement starts
        endline (int): The number of the line at which the replacement stops
        lines_list list[string]: The list of the new lines to be written to the file

    Returns:
        str: Success message or error message if it was not successful
    """
    logger.debug("write_fix: starting fix validation")
    if len(changes_dicts) == 0:
        return "The fix you passed is empty. Please provide a non empty implementation of the fix."

    try:
        logger.debug("write_fix: extracting targeted lines from changes_dicts")
        target_lines = extract_targeted_lines(changes_dicts)
        logger.debug("write_fix: fetching list of known buggy lines")
        buggy_lines = get_list_of_buggy_lines(project_name, bug_index)
        logger.debug("write_fix: computing missed buggy lines")
        missed_lines = set(buggy_lines) - set(target_lines)
    except (KeyError, ValueError, TypeError) as e:
        logger.warn(f"write_fix: failed to compute missed lines: {e}")
        missed_lines = []

    if not agent.dummy_fix:
        logger.debug("write_fix: creating deletion template for dummy fix test")
        deletion_fix = create_deletion_template(project_name, bug_index)
        logger.debug("write_fix: deletion template created, checking if applicable")
        if deletion_fix is not None:
            run_ret = execute_write_range(project_name, bug_index, deletion_fix, agent)
            logger.debug("write_fix: deletion template applied, checking test results")
            agent.dummy_fix = True
            if " 0 failing test" in run_ret:
                return "Deleting the buggy lines fixed the problem and passed all the test cases. 0 failing tests."
    if len(missed_lines)!=0:
        logger.debug(f"write_fix: {len(missed_lines)} buggy lines not targeted by fix")
        fix_template = create_fix_template(project_name, bug_index)
        logger.debug("write_fix: fix template created for missed lines")
        return "Your fix did not target all the buggy lines. Here is the list of all the buggy lines: {}. To help you, you can fill out the following the template to generate your fix {}".format(buggy_lines, fix_template)
    run_ret = execute_write_range(project_name, bug_index, changes_dicts, agent)
    return run_ret + "\n **Note:** You are automatically switched to the state 'trying out candidate fixes'"
    
def execute_read_range(project_name, bug_index, filepath, startline, endline, agent):
    workspace = agent.config.workspace_path
    project_dir = os.path.join(workspace, project_name.lower()+"_"+str(bug_index)+"_buggy")
    filepath = preprocess_paths(agent, project_name, bug_index, filepath)
    with open(os.path.join(project_dir,filepath)) as fp:
        lines = fp.readlines()

    lines_str = ""
    for i in range(startline-1, endline, 1):
        if i >= len(lines):
            lines_str += "EOF"
            break
        lines_str+="Line {}:".format(i+1) + lines[i]
    return lines_str


def execute_write_range(project_name, bug_index, changes_dicts, agent):
    project_dir = os.path.join(agent.config.workspace_path, project_name.lower()+"_"+str(bug_index)+"_buggy")
    for change_dict in changes_dicts:
        resolved = dict(change_dict)
        filepath = resolved["file_name"]
        filepath = preprocess_paths(agent, project_name, bug_index, filepath)
        resolved["file_name"] = os.path.join(project_dir, filepath)

        apply_changes(resolved)

    run_ret = run_defects4j_tests(project_name, bug_index, agent)
    return "Lines written successfully, the result of running test cases on the modified code is the following:\n" + run_ret

def get_edited_files(name, index):
    target_file = "defects4j/framework/projects/{name}/patches/{index}.src.patch".format(name=name, index=index)
    with open(target_file) as ptf:
        diff_content = ptf.readlines()

    files_list = []
    for line in diff_content:
        if line.startswith("diff --git"):
            files_list.append(extract_file_name(line))
    return files_list

def extract_file_name(diff_line):
    diff_line = diff_line.split(" ")
    return "/".join(diff_line[2].split("/")[1:])


def extract_lines_range(name, index):
    import whatthepatch
    target_file = "defects4j/framework/projects/{name}/patches/{index}.src.patch".format(name=name, index=index)
    with open(target_file) as ptf:
        text = ptf.readlines()
    diff = [x for x in whatthepatch.parse_patch(text)]
    min_max = []
    for diff0 in diff:
        max_line = 0
        min_line = float('inf')
        for d in diff0.changes:
            if d.new is not None:
                if d.new < min_line:
                    min_line = d.new
                if d.new > max_line:
                    max_line = d.new
        min_max.append((min_line, max_line-5))
    return min_max


@command(
    "get_classes_and_methods",
    "This function allows you to get all classes and methods names within a file.\
    It returns a dictionary where keys are classes names and values are list of methods names\
    The file path should start from source or src directory depending on the project, you whould know which one is it after you execute get_info command",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project under scope",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you are trying to fix.",
            "required": True

        },
        "file_path":{
            "type": "string",
            "description": "the path to the file that is for which you want to extract the classes and functions",
            "required": True
        }
    },
)
def get_classes_and_methods(project_name: str, bug_index: str, file_path: str, agent: Agent):
    """This function allows you to get all classes and methods names within a file. 
    It returns a dictionary where keys are classes names and values are list of methods names"""
    
    workspace = agent.config.workspace_path
    project_dir="{}_{}_buggy".format(project_name.lower(), bug_index)
    source_dir = ""
    if os.path.exists(os.path.join(workspace, project_dir, "source")):
        source_dir = "source"
    elif os.path.exists(os.path.join(os.path.join(workspace, project_dir, "src"))):
        source_dir = "src"
    else:
        pass
    file_path = preprocess_paths(agent, project_name, bug_index, file_path)
    with open(os.path.join(workspace, project_dir, file_path)) as tfp:
        content = tfp.read()

    tree = javalang.parse.parse(content)

    classes = {}
    for path, node in tree:
        if isinstance(node, javalang.tree.ClassDeclaration):
            classes[node.name] = []
            for method in node.methods:
                classes[node.name].append(method.name)
    return str(classes)

def list_files(start_path='.'):
    file_list = []
    for root, dirs, files in os.walk(start_path):
        for file in files:
            if file.endswith(".java"):
                file_path = os.path.join(root, file)
                file_list.append(file_path)
    return file_list

@command(
    "search_code_base",
    "This function will seach in all java files for a provided list of keywords, it will return a dictionary where for each file\
    it will give the classes and within the classes the methods names and within the methods names a list of matched keywords against the method name\
    the returned results looks structurly like this { file_name: { class_name: { method_name: [...list of matched keywords...] } } } \
    this function is useful to search for already implemented methods that could be reused or to look for similar code to get an idea on how\
    to implement a certain functionality. This function does not return the code itself but just the matched methods names that contain at least one of the keywords.",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project under scope",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you are trying to fix.",
            "required": True

        },
        "key_words":{
            "type": "list",
            "description": "The list of keywords for which you want to find a match in the code base",
            "required": True
        }
    },
)

def search_code_base(project_name:str, bug_index:str, key_words: list, agent: Agent):
    workspace = agent.config.workspace_path
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)

    source_dir = ""
    all_dirs = os.listdir(os.path.join(workspace, project_dir))
    if "src" in all_dirs:
        source_dir = "src"
    else:
        source_dir = "source"

    java_files = list_files(os.path.join(workspace, project_dir))
    new_keywords = key_words
    #for word in key_words:
    #    new_keywords.extend(re.split('(?<=.)(?=[A-Z])', word))
    
    split_simple = []
    for word in new_keywords:
        split_simple.extend(word.split("_"))

    split_dot = [word for word in split_simple]
    for word in split_simple:
        split_dot.append(word.split(".")[-1])

    lower_kwords = [kw.lower().replace("(", "").replace(")", "") for kw in split_dot]
    
    matched_files = {}
    for file in java_files:
        #logger.debug("searching file: " + file)
        with open(file, encoding='utf-8', errors='ignore') as jf:
            content = jf.read()
        tree = javalang.parse.parse(content)
        for path, node in tree:
            if isinstance(node, javalang.tree.ClassDeclaration):
                class_name = node.name
                #logger.debug("searching class: " + class_name)
                # Extract information about methods within the class
                for method_declaration in node.methods:
                    method_name = method_declaration.name
                    #logger.debug("searching method: " + method_name)
                    # Extract the code of the method
                    #method_code = content[method_declaration.position[0]: method_declaration.position[1]]
                    #method_code = method_declaration.body
                    #logger.debug(str(method_declaration.position))
                    #lower_code = method_code.lower()
                    matched_keywords = []
                    for kw in lower_kwords:
                        if kw in method_name.lower():
                            matched_keywords.append(kw)
                    if matched_keywords:
                        if file in matched_files:
                            if class_name in matched_files[file]:
                                matched_files[file][class_name][method_name] = matched_keywords
                            else:
                                matched_files[file][class_name]={method_name:matched_keywords}
                        else:
                            matched_files[file] = {class_name:{method_name:matched_keywords}}
    logger.debug(str(matched_files))
    matched_names = [f for f in java_files if f.endswith(".java") and any(k in f.lower() for k in lower_kwords)]
    return "The following matches were found:\n"+str(matched_files) + "\nThe search also matched the following files names: \n" + "\n".join(matched_names)


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


@command(
    "extract_test_code",
    "This function allows you to extract the code of the failing test cases which will help you understand the test case that led to failure\
    for example by looking at the assertions and the given input and expected output. This command should be executed at most one time",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project under scope",
            "required": True,
        },
        "bug_index":{
            "type": "integer",
            "description": "The index (number) of the bug that you are trying to fix.",
            "required": True

        },
        "test_file_path":{
            "type": "string",
            "description": "The path to the test file",
            "required": True

        }
    }
)
def extract_test_code(project_name:str, bug_index:str, test_file_path: str, agent:Agent):

    workspace = agent.config.workspace_path
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
    test_dir = ""
    all_dirs = os.listdir(os.path.join(workspace, project_dir))
    test_file_path = test_file_path.split("::")[0]
    if test_file_path.endswith(".java"):
        test_file_path = test_file_path[:-5]
        test_file_path = test_file_path.replace(".", "/")
        test_file_path += ".java"
    else:
        test_file_path = test_file_path.replace(".", "/")

    with open(os.path.join(workspace, project_dir+"_test.txt")) as testf:
        test_message = testf.read()
    logger.debug(test_message)
    result = extract_failing_test(test_message)
    if not result:
        return "No test function found, probably the failing test message was not parsed correctly"
    
    
    if not os.path.exists(os.path.join(workspace, project_dir, test_dir, test_file_path)):
        if not os.path.exists(os.path.join(workspace, project_dir, "files_index.txt")):
            with open(os.path.join(workspace, project_dir, "files_index.txt"), "w") as fit:
                fit.write("\n".join(list_java_files(os.path.join(workspace, project_dir))))
                
        with open(os.path.join(workspace, project_dir, "files_index.txt")) as fit:
            files_index = [f for f in fit.read().splitlines() if test_file_path in f]

        if len(files_index) == 1:
            test_file_path = files_index[0]
        elif len(files_index) >= 1:
            raise ValueError("Multiple Candidate Paths. We do not handle this yet!")
        else:
            return "The filepath {} does not exist.".format(test_file_path)
        
    if not test_file_path:
        return "You should provide the test file path"
        class_name = result["class_name"]
        path = "/".join(class_name.split("."))+".java"
        logger.debug(path)
        if os.path.exists(os.path.join(workspace, project_dir, "test", path)):
            test_file_path = os.path.join(workspace, project_dir, "test", path)
        elif os.path.exists(os.path.join(workspace, project_dir, "tests", path)):
            test_file_path = os.path.join(workspace, project_dir, "tests", path)
        else:
            results = search_code_base(project_name, bug_index, [class_name], agent)
            results= json.loads(results.replace("The following matches were found:\n", ""))
            if results:
                test_file_path = list(results.keys())[0]
            else:
                return "Could not find the test file, something went wrong."
    
    else:
        test_file_path = os.path.join(agent.config.workspace_path, project_dir, test_dir, test_file_path)



    with open(test_file_path, 'r') as file:
        file_content = file.read()
    
    function_name = result["function_name"]
    ind = file_content.find("public void {}".format(function_name))
    if ind == -1:
        return None
    file_content = file_content[ind:]
    ind2 = file_content[len("public void "):].find("public void ")
    if ind2 == -1:
        return file_content
    else:
        return file_content[:ind2+len("public void ")]


def extract_fail_report(name: str, index: str, agent: Agent):
    project_dir = "{}_{}_buggy".format(name.lower(), index)
    workspace = agent.config.workspace_path

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
            if "::" not in line:
                raise ValueError(f"Expected '::' separator in test case line: {line}")
            case_base = line[4:line.find("::")]
            case_base = ".".join(case_base.split(".")[:-1])
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

def prepare_init_file(root_path, root_uri, workspace_folder, workspace, project_dir):
    with open("lsp_init_template.json") as lit:
        lsp_template = json.load(lit)

    lsp_template["params"]["rootPath"] = root_path
    lsp_template["params"]["rootUri"] = root_uri
    lsp_template["params"]["initializationOptions"]["workspaceFolders"] = [workspace_folder]
    lsp_template["params"]["workspaceFolders"][0]["uri"] = workspace_folder
    lsp_template["params"]["workspaceFolders"][0]["name"] = project_dir

    with open(os.path.join(workspace, project_dir, "lspeclipse", "lsp_init_file.json"), "w") as json_handler:
        json.dump(lsp_template, json_handler)

def execute_command(command, init_req, req):
    # Open the subprocess with stdout redirected to a file
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stdin=subprocess.PIPE, text=True, shell=True)
    content_length = len(init_req)
    request = "Content-Length: {}\r\n\r\n{}".format(content_length, init_req)
    logger.debug(f"LSP init request: {request}")
    # Send the input to the subprocess
    process.stdin.write(request)

    time.sleep(3)
    content_length = len(req)
    request = "Content-Length: {}\r\n\r\n{}".format(content_length, req)
    logger.debug(f"LSP request: {request}")
    process.stdin.flush()
    process.stdin.write(request)
    #process.stdin.flush()
    time.sleep(2)
    process.kill()

def prepare_command(workspace, project_dir):
    cmd = ['cd {} &&'.format(os.path.join(workspace, project_dir, "lspeclipse")),
        '/usr/lib/jvm/java-17-openjdk-amd64/bin/java',
        '-Declipse.application=org.eclipse.jdt.ls.core.id1',
        '-Dosgi.bundles.defaultStartLevel=4',
        '-Declipse.product=org.eclipse.jdt.ls.core.product',
        '-Dlog.level=ALL',
        '-Xmx1G',
        '--add-modules=ALL-SYSTEM',
        '--add-opens java.base/java.util=ALL-UNNAMED',
        '--add-opens java.base/java.lang=ALL-UNNAMED',
        '-jar',
        './plugins/org.eclipse.equinox.launcher_1.6.600.v20231012-1237.jar',
        '-configuration',
        './config_linux',
        '-data',
        './workspace',
        '> lsp_output.txt'
    ]
    return " ".join(cmd)

def prepare_lsp_env(name, index, workspace):
    source_path = "lspeclipse"
    destination_path = os.path.join(workspace, "_".join([name.lower(), str(index), "buggy"]))

    # Using subprocess to execute the cp command
    command = ["cp", "-r", source_path, destination_path]

    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to copy LSP environment: {e}")



def lsp_hover(name:str, index:str, file_path:str, line_number:int, column:int, agent: Agent):
    base_dir = os.path.abspath(".")
    workspace = agent.config.workspace
    project_dir = "_".join([name.lower(), str(index), "buggy"])
    id = random.randint(100, 9999999999)
    hover_request = {
        "jsonrpc": "2.0",
        "id": id,
        "method": "textDocument/hover","params": {
	        "textDocument": {
		        "uri": "file:///{base_dir}/{workspace}/{project_dir}/{file_path}".format(
                    base_dir=base_dir, workspace=workspace, project_dir=project_dir, file_path=file_path)
	        },
	        "position": {
		    "line": line_number,
		    "character": column
	        }
        }}

    string_request = json.dumps(hover_request)
    command = prepare_command(workspace, project_dir)
    logger.debug("COMMAND: " + command)
    if not os.path.exists(os.path.join(workspace, project_dir, "lspeclipse")):
        prepare_lsp_env(name, index, workspace)

    if not os.path.exists(os.path.join(workspace, project_dir, "lspeclipse", "lsp_init_file.json")):
        root_path = str(os.path.join(base_dir, workspace, project_dir))
        root_uri = "file://" + root_path
        workspace_folder = root_uri

        prepare_init_file(root_path, root_uri, workspace_folder, workspace, project_dir)

    with open(os.path.join(workspace, project_dir, "lspeclipse", "lsp_init_file.json")) as inif:
        init_content = inif.read()

    execute_command(command, init_content, string_request)

    if not os.path.exists(os.path.join(workspace, project_dir, "lsp_output.txt")):
        return "ERROR NO OUTPUT: LSP command was not executed correctly, shutting down LSP server, do not use again."
    else:
        with open(os.path.join(workspace, project_dir, "lsp_output.txt")) as lspf:
            tmpf_content = lspf.read()

        if len(tmpf_content) <2:
            return "ERROR EMPTY OUTPUT: LSP command was not executed correctly, shutting down LSP server, do not use again."
        else:
            return tmpf_content


## TO BE PUT TEMPORARILY HERE

from langchain.chat_models import ChatOpenAI
from langchain.schema.messages import HumanMessage, SystemMessage, AIMessage

"""@command(
    "ask_chatgpt",
    "This function allows you to ask chatgpt any question. Chatgpt is LLM that has amazing question answering abilities.\
    strucutre your question as following ## Summary of the problem: PUT SUMMARY OF THE PROBLEM HERE ## Possible buggy code: HERE YOU PUT THE BUGGY CODE SNIPET, ## Failing test cases and test result: HERE PUT THE RESULT OF EXECUTING TEST CASES AND THE CODE OF THE FAILING CASE",
    {
        "question": {
            "type": "string",
            "description": "The name of the project under scope",
            "required": True,
        },
    }
)
"""
def ask_chatgpt(question: str, agent: Agent):
    chat = ChatOpenAI(model=agent.config.static_llm)

    if not agent.ask_chatgpt:
        messages = [
        SystemMessage(content="You're a helpful assistant who answer questions mostly related to programming, software, debugging, code repair, code generation, code implementation in all possible languages, you also a big base of knowledge regarding programming and software.\
If the details in the given quetion are not enough, you should ask the user to add more details and ask again."),
        HumanMessage(content=question),
    ]
        agent.ask_chatgpt = messages
    else:
        messages = agent.ask_chatgpt
        messages.append(HumanMessage(content=question))

    response = chat.invoke(messages)
    agent.ask_chatgpt.append(response)

    return response.content

def validate_fix_against_hypothesis(bug_report, hypothesis, fix, model):
    chat = ChatOpenAI(model=model)

    messages = [
        SystemMessage(
            content="You are a helpful assistant in coding and debugging tasks." +\
                    "Particularly, you will be given some information about a bug," +\
                    "a hypothesis about the bug made by a person and the fix suggested by that person."+\
                    "Based on the given information, you should check whether the suggested fix is consistent with hypothesis."+\
                    "In case the fix does not reflect the hypothesis or it contradicts the information given about the bug, you should explain and suggest a better fix."
                    ),
        HumanMessage(
            content=bug_report + "\n" +\
                     "## Hypothesis\n"+\
                     f"{hypothesis}\n"+\
                     "## Suggested fix\n"+\
                     f"{fix}\n"+\
                     "Is the fix consistent with the hypothesis? Does the hypothesis about the bug make sense? Also, check if the lines numbers are consistent or not and if some lines are unnecessarily changed or rewritten. For example, if the buggy line is line 445, it would make sense to change that line only. If not, explain why and suggest a correction. Keep your answer very short and concise."
            )  
    ]
    response = chat.invoke(messages)

    return response.content

def remove_comments(java_code):
    # Remove both single-line and multi-line comments
    pattern = re.compile(r'(/\*.*?\*/|//.*?$)', re.MULTILINE | re.DOTALL)
    return re.sub(pattern, '', java_code)

def extract_function_calls(java_code):

    java_code = remove_comments(java_code)
    # Define a pattern to match function or method calls, excluding if and while conditions
    pattern = re.compile(r'\b(?:(?!if|while)\w+\s*\(.*?\))')

    # Find all matches in the Java code
    matches = pattern.findall(java_code)

    logger.info(list(set(matches)))
    # Print the matches
    return [match for match in matches]

@command(
    "extract_similar_functions_calls",
    "For a provided buggy code snippet in 'code_snippet' within the file 'file_path', this function extracts similar function calls. This aids in understanding how functions are utilized in comparable code snippets, facilitating the determination of appropriate parameters to pass to a function.",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project",
            "required": True
        },
        "bug_index": {
            "type": "string",
            "description": "The bug index",
            "required":True
        },
        "file_path": {
            "type": "string",
            "description": "The path of the file containing the buggy snippet",
            "required": True,
        },
        "code_snippet":{
            "type": "string",
            "description": "the buggy code snippet",
            "required": True
        }
    }
)

def extract_similar_functions_calls(project_name:str, bug_index: str, file_path: str, code_snippet: str, agent:Agent):
    workspace = agent.config.workspace_path
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)

    file_path = preprocess_paths(agent, project_name, bug_index, file_path)
    with open(os.path.join(workspace, project_dir, file_path)) as fpt:
        java_code = fpt.read()

    all_calls = extract_function_calls(java_code)
    calls = extract_function_calls(code_snippet)
    #logger.debug("ALL CALLS: " + str(all_calls))
    #logger.debug("CALLS: " + str(calls))
    if not calls:
        return "No function calls were found. There is no need to call this command again."
    similar_calls = {}
    for c in calls:
        ec = c[:c.find('(')]
        similar_calls[c] = []
        for ac in all_calls:
            if (ec in ac) and c!=ac:
                similar_calls[c].append(ac)

    logger.debug("SIMILAR: "+str(similar_calls))
    for c in similar_calls:
        if similar_calls[c]:
            break
    else:
        return "No similar functions calls were found. There is no need to use this command again."
    
    return "The following similar calls were found. The keys of the dictionary are calls from the code snippet, and the values are similar calls from the file.\n"+str(similar_calls)


def get_localization(name, index):
    localization_dir = "defects4j/buggy-lines"
    methods_dir = "defects4j/buggy-methods"
    file_name = "{}-{}.buggy.lines".format(name, index)
    if not os.path.exists(os.path.join(localization_dir, file_name)):
        lines_info = ""
    else:
        with open(os.path.join(localization_dir, file_name)) as buggy_lines_file:
            bug_lines = buggy_lines_file.read()
        lines_info = "The bug is located at exactly these lines numbers: (the format is file-name#line-number# line-code):\n" + bug_lines

    file_name = "{}-{}.buggy.methods".format(name, index)
    if not os.path.exists(os.path.join(methods_dir, file_name)):
        methods_info = ""
    else:
        methods_info = "The following is the list of buggy methods:\n"
        with open(os.path.join(methods_dir, file_name)) as methods:
            methods_list = methods.read().splitlines()

        for m in methods_list:
            if m.endswith("1"):
                methods_info += m +'\n'
    return lines_info + "\n" + methods_info


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
        try:
            method_name = ctx.Identifier().getText()
            method_body = ctx.methodBody().getText()
            method_params = ctx.formalParameters().getText()
            start_index = (ctx.start.line, ctx.start.column)
            end_index = (ctx.stop.line, ctx.stop.column)
            if method_name == self.target_name:
                self.matched_methods.append((method_name, method_body, method_params, start_index, end_index))
        except Exception as e:
            logger.debug(f"FunctionExtractor: failed to extract method: {e}")

@command(
    "extract_method_code",
    "This command allows you to extract possible implementation of a given method name inside a file.",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project",
            "required": True
        },
        "bug_index": {
            "type": "string",
            "description": "The bug index",
            "required":True
        },
        "filepath": {
            "type": "string",
            "description": "The path of the file",
            "required": True,
        },
        "method_name":{
            "type": "string",
            "description": "the name of the method to extract",
            "required": True
        }
    }
)

def extract_method_code(project_name: str, bug_index: str, filepath: str, method_name:str, agent: Agent):
    workspace = agent.config.workspace_path
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
    filepath = preprocess_paths(agent, project_name, bug_index, filepath)

    input_stream = FileStream(os.path.join(workspace, project_dir, filepath))
    
    lexer = JavaLexer(input_stream)
    token_stream = CommonTokenStream(lexer)
    parser = JavaParser(token_stream)
    
    tree = parser.compilationUnit()
    
    extractor = FunctionExtractor()
    extractor.target_name = method_name
    walker = ParseTreeWalker()
    walker.walk(extractor, tree)
    ret_val = "We found the following implementations for the method name {} (we give the body of the method):\n".format(method_name)
    with open(os.path.join(workspace, project_dir, filepath)) as wpf:
        file_content = wpf.read().splitlines()
    
    for i, m in enumerate(extractor.matched_methods):
        ret_val += "### Implementation candidate {}:\n".format(i)
        ret_val += "\n".join(file_content[m[-2][0]-1: m[-1][0]])
        ret_val += "\n"
    return ret_val

import tiktoken
from unittest.mock import MagicMock

def extract_function_def_context(project_name, bug_index, method_name, filepath, agent):
    input_limit = 12000
    workspace = "./auto_gpt_workspace"
    project_dir = "{}_{}_buggy".format(project_name.lower(), bug_index)
    filepath = preprocess_paths(agent, project_name, bug_index, filepath)
    extracted_methods = extract_method_code(project_name, bug_index, filepath, method_name, agent)
    if len(extracted_methods) == 0:
        raise ValueError("NO EXTRACTED METHODS, SHOULD NOT HAPPEN")
    
    method_body = extracted_methods[0]
    with open(os.path.join(workspace, project_dir, filepath)) as wpf:
        file_content = wpf.read()

    start_index = file_content.find(method_body)
    if start_index == -1:
        raise ValueError("METHOD BODY NOT FOUND, INDEX = -1, SHOULD NOT HAPPEN")
    context = file_content[:start_index]
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    encoded_context = enc.encode(context)
    if len(encoded_context) < input_limit:
        return context
    else:
        return enc.decode(encoded_context[-input_limit:])

@command(
    "AI_generates_method_code",
    "This function allows to use an AI Large Language model to generate the code of the buggy method (Autocomplete code). params: (project_name: str, bug_index: str, filepath: str, method_name: str)",
    {
        "project_name": {
            "type": "string",
            "description": "The name of the project",
            "required": True
        },
        "bug_index": {
            "type": "string",
            "description": "The bug index",
            "required":True
        },
        "filepath": {
            "type": "string",
            "description": "The path of the file",
            "required": True,
        },
        "method_name":{
            "type": "string",
            "description": "the name of the method to extract",
            "required": True
        }
    }
)
def auto_complete_functions(project_name, bug_index, filepath, method_name, agent):
    context = extract_function_def_context(project_name, bug_index, method_name, filepath, agent)
    chat = ChatOpenAI(model=agent.config.static_llm)
    messages = [
            SystemMessage(
                content="You are a code implementer and autocompletion engine. Basically, you would be given some already written code up to some line and you would be asked to implement the function/method that is declared at the last line. Always give full implementation of the method starting from declaration (public void myFunc(...)) to all the body. Take the given context into considration. Only give the implementation of the method and nothing else. If you want to add some explanation you can write it as comments above each line of code."),
            HumanMessage(
                content="Implement the code for the method {}. Here is the code preceeding the method definition:\n{}".format(method_name, context))
        ]
        #response_format={ "type": "json_object" }
    response = chat.invoke(messages)
    return response.content

from fuzzywuzzy import fuzz
def apply_changes(change_dict):
    file_name = change_dict.get("file_name", "")
    insertions = change_dict.get("insertions", [])
    deletions = change_dict.get("deletions", [])
    modifications = change_dict.get("modifications", [])

    # Read the original code from the file
    with open(file_name, 'r') as file:
        lines = file.readlines()

    # Apply deletions first to avoid conflicts with line number changes
    affected_lines = set()
    for line_number in deletions:
        if 1 <= int(line_number) <= len(lines):
            lines[int(line_number) - 1] = "\n"

    # Apply modifications
    for modification in modifications:
        line_number = modification.get("line_number", 0)
        modified_line = modification.get("modified_line", "")
        if 1 <= int(line_number) <= len(lines):
            orig_line = lines[int(line_number) - 1]
            if fuzz.ratio(orig_line, modified_line) < 70:
                continue
            if modified_line.endswith("\n"):
                lines[int(line_number) - 1] = modified_line
            else:
                lines[int(line_number) - 1] = modified_line + "\n"

    # Apply insertions and record affected lines
    line_offset = 0
    from operator import itemgetter

    sorted_insertions = sorted(insertions, key=itemgetter('line_number')) 
    for insertion in sorted_insertions:
        line_number = int(insertion.get("line_number", 0)) + line_offset
        for new_line in insertion.get("new_lines", []):
            lines.insert(int(line_number) - 1, new_line)
            line_number += 1
            line_offset += 1


    # Write the modified code back to the file
    with open(file_name, 'w') as file:
        file.writelines(lines)

    return affected_lines

def extract_targeted_lines(changes_dicts):
    targeted_lines = []
    for cd in changes_dicts:
        insertions = cd.get("insertions", [])
        deletions = cd.get("deletions", [])
        modifications = cd.get("modifications", [])
        targeted_lines.extend(deletions)
        targeted_lines.extend([d["line_number"] for d in modifications])
        targeted_lines.extend([d["line_number"] for d in insertions])
    
    return [int(i) for i in targeted_lines]

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
            lines.append(int(bl.split("#")[-2]))
        return lines