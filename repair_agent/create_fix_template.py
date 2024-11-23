import json

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
	fix_template_str = fix_template_str.replace('"insertions": []', '"insertions": [here put the list of insertion dictionaries to add new lines of code: {"line_numbe":..., "new_lines":[...]}, ...]')
	return fix_template_str

print(create_fix_template("Closure", 34))