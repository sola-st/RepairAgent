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
        # The position must advance with each inserted line. Holding it fixed
        # inserts every line of a block at the same index, which writes the
        # block out in reverse and turns any multi-line fix into invalid code.
        # max(0, ...) keeps a malformed or missing line_number (which defaults
        # to 0) from becoming a negative index: list.insert(-1, x) silently
        # places the line before the LAST line and splits the block apart.
        position = max(0, int(insertion.get("line_number", 0)) + line_offset - 1)
        for new_line in insertion.get("new_lines", []):
            lines.insert(position, new_line)
            position += 1
            line_offset += 1


    # Write the modified code back to the file
    with open(file_name, 'w') as file:
        file.writelines(lines)

    return affected_lines