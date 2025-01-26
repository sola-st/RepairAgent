import os

def replace_placeholder(file_path, placeholder, new_value):
    """
    Replace all occurrences of a new value in a file with a placeholder.
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read()

        updated_content = content.replace(new_value, placeholder)

        with open(file_path, 'w') as file:
            file.write(updated_content)

        print(f"Replaced {new_value} with {placeholder} in {file_path}")
    except Exception as e:
        print(f"Failed to update {file_path}: {e}")


def main():
    files_and_placeholders = [
        ("autogpt/commands/defects4j_static.py", "API-KEY-PLACEHOLDER"),
        ("autogpt/commands/defects4j.py", "API-KEY-PLACEHOLDER"),
        ("autogpt/.env", "GLOBAL-API-KEY-PLACEHOLDER"),
        ("run.sh", "GLOBAL-API-KEY-PLACEHOLDER"),
        (".env", "GLOBAL-API-KEY-PLACEHOLDER"),
    ]

    # Read the replacement value from token.txt
    try:
        with open("token.txt", "r") as token_file:
            replacement_value = token_file.read().strip()
    except FileNotFoundError:
        print("Error: token.txt not found. Please run the first script to generate it.")
        return

    # Restore placeholders in files
    for file_path, placeholder in files_and_placeholders:
        replace_placeholder(file_path, placeholder, replacement_value)


if __name__ == "__main__":
    main()