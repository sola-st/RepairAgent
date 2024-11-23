import json


## trying out candidate fixes
write_fix_desc = """write_fix: Use this command to implement the fix you came up with. The test cases are run automatically after writing the changes. The changes are reverted automatically if the the test cases fail. This command requires the following params: (project_name: string, bug_index: integer, changes_dicts:list[dict]) where changes_dict is a list of dictionaries in the format defined in section '## The format of the fix'.The list should contain at least one non empty dictionary of changes as defined below. If you are not already in the state 'trying out candidate fixes', by calling this command you will automatically switch that state. [RESPECT LINES NUMBERS AS GIVEN IN THE LIST OF READ LINES SECTIONS]"""

try_fixes_desc = """try_fixes: This is a very useful command when you want to try multiple fixes quickly. This function allows you to try a list of fixes, the function will execute related tests to see if any of the fixes work. Each fix should respect the fix format defined in section '## The format of the fix'. The list of params to pass to this command are: (project_name: str, bug_index: int, fixes_list: list[fix as defined below])"""

read_range_desc = """read_range: Read a range of lines in a given file, parms:(project_name:string, bug_index:string, filepath:string, startline: int, endline:int) where project_name is the name of the project and bug_index is the index of the bug"""

go_back_desc = """go_back_to_collect_more_info: This command allows you to go back to the state 'collect information to fix the bug'. Call this command after you have suggested many fixes but none of them worked, params: (reason_for_going_back: string)"""

discard_hypothesis = """discard_hypothesis: This command allows you to discard the hypothesis that you made earlier about the bug and automatically return back again to the state 'collect information to uderstand the bug' where you can express a new hypothesis, params: (reason_for_discarding: string), calling this command will automatically change the state to 'collect information to understand the bug'"""

goals_accomplished_desc = """goals_accomplished: Call this function when you are sure you fixed the bug and all tests hava passed and give the reason that made you believe that you fixed the bug successfully, params: (reason: string)"""

## collect information to fix the bug

search_code_desc = """search_code_base: This utility function scans all Java files within a specified project for a given list of keywords. It generates a dictionary as output, organized by file names, classes, and method names. Within each method name, it provides a list of keywords that match the method's content. The resulting structure is as follows: { file_name: { class_name: { method_name: [...list of matched keywords...] } } }. This functionality proves beneficial for identifying pre-existing methods that may be reusable or for locating similar code to gain insights into implementing specific functionalities. It's important to note that this function does not return the actual code but rather the names of matched methods containing at least one of the specified keywords. It requires the following params params: (project_name: string, bug_index: integer, key_words: list). Once the method names are obtained, the extract_method_code command can be used to retrieve their corresponding code snippets (only do it for the ones that are relevant)"""

get_classes_desc = """get_classes_and_methods: This function allows you to get all classes and methods names within a file. It returns a dictinary where keys are classes names and values are list of methods names within each class. The required params are: (project_name: string, bug_index: integer, file_path: string)"""

get_similar_desc = """extract_similar_functions_calls: For a provided buggy code snippet in 'code_snippet' within the file 'file_path', this function extracts similar function calls. This aids in understanding how functions are utilized in comparable code snippets, facilitating the determination of appropriate parameters to pass to a function., params: (project_name: string, bug_index: string, file_path: string, code_snippet: string)"""

extract_method_desc = """extract_method_code: This command allows you to extract possible implementations of a given method name inside a file. The required params to call this command are: (project_name: string, bug_index: integer, filepath: string, method_name: string)"""

generate_method_desc = "AI_generates_method_code: This function allows to use an AI Large Language model to generate the code of the buggy method. This helps see another implementation of that method given the context before it which would help in 'probably' infering a fix but no garantee. params: (project_name: str, bug_index: str, filepath: str, method_name: str) "
### also write fix

## collect information to understand the bug
extract_test_desc = """extract_test_code: This function allows you to extract the code of the failing test cases which will help you understand the test case that led to failure for example by looking at the assertions and the given input and expected output, params: (project_name: string, bug_index: integer, test_file_path: string). You are allowed to execute this command for once only, unless it returns an error message, in which case you can try again with different arguments."""

### also read range

express_hypo_desc = """ express_hypothesis: This command allows to express a hypothesis about what exactly is the bug. Call this command after you have collected enough information about the bug in the project, params: (hypothesis: string). By calling this command, you also automatically switch to the state 'collect information to fix the bug'. Before delving into fixing, you should always express a hypothesis."""

commands_dict = {
    "trying out candidate fixes": "\n".join(["{}. {}".format(i+1, t) for i, t in enumerate(
        [write_fix_desc, read_range_desc, go_back_desc, discard_hypothesis, goals_accomplished_desc])]),
    "collect information to fix the bug": "\n".join(["{}. {}".format(i+1, t) for i, t in enumerate(
        [search_code_desc, get_classes_desc, get_similar_desc, extract_method_desc, write_fix_desc, read_range_desc, generate_method_desc])]),
    "collect information to understand the bug": "\n".join(["{}. {}".format(i+1, t) for i, t in enumerate(
        [extract_test_desc, express_hypo_desc, read_range_desc])])
}

with open("commands_by_state.json", "w") as cbs:
    json.dump(commands_dict, cbs)