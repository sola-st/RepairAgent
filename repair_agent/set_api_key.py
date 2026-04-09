import os


def replace_placeholder(file_path, placeholder, new_value):
    """
    Replace all occurrences of a placeholder in a file with a new value.
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read()

        updated_content = content.replace(placeholder, new_value)

        with open(file_path, 'w') as file:
            file.write(updated_content)

        print(f"Updated {placeholder} in {file_path}")
    except Exception as e:
        print(f"Failed to update {file_path}: {e}")


def set_env_var(file_path, key, value):
    """
    Set or update an environment variable in a .env file.
    """
    try:
        lines = []
        found = False
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                lines = f.readlines()

        new_lines = []
        for line in lines:
            if line.strip().startswith(f"{key}="):
                new_lines.append(f"{key}={value}\n")
                found = True
            else:
                new_lines.append(line)

        if not found:
            new_lines.append(f"{key}={value}\n")

        with open(file_path, 'w') as f:
            f.writelines(new_lines)

        print(f"Set {key} in {file_path}")
    except Exception as e:
        print(f"Failed to update {file_path}: {e}")


def main():
    print("Which LLM provider will you use?")
    print("  1. OpenAI (GPT models)")
    print("  2. Anthropic (Claude models)")
    print("  3. Both")
    choice = input("Enter 1, 2, or 3: ").strip()

    env_files = [".env", "autogpt/.env"]

    if choice in ("1", "3"):
        openai_key = input("OpenAI API key: ").strip()
        if openai_key:
            for env_file in env_files:
                set_env_var(env_file, "OPENAI_API_KEY", openai_key)
            # Also update run.sh placeholder if present
            replace_placeholder("run.sh", "GLOBAL-API-KEY-PLACEHOLDER", openai_key)
            # Save to token.txt for backwards compatibility
            with open("token.txt", "w") as token_file:
                token_file.write(openai_key)
        else:
            print("Skipped OpenAI API key.")

    if choice in ("2", "3"):
        anthropic_key = input("Anthropic API key: ").strip()
        if anthropic_key:
            for env_file in env_files:
                set_env_var(env_file, "ANTHROPIC_API_KEY", anthropic_key)
        else:
            print("Skipped Anthropic API key.")

    if choice not in ("1", "2", "3"):
        # Backwards compatible: assume OpenAI
        print("\nDefaulting to OpenAI setup.")
        replacement_value = input("OpenAI API key: ").strip()

        if replacement_value:
            for env_file in env_files:
                set_env_var(env_file, "OPENAI_API_KEY", replacement_value)
            replace_placeholder("run.sh", "GLOBAL-API-KEY-PLACEHOLDER", replacement_value)
            with open("token.txt", "w") as token_file:
                token_file.write(replacement_value)

    print("\nDone! You can now run RepairAgent.")


if __name__ == "__main__":
    main()
