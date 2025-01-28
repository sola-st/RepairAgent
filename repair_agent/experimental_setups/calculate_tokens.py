import os
import re
import tiktoken
import statistics
import matplotlib.pyplot as plt

def calculate_tokens(folder_path, fixed_file_path, model_name="gpt-3.5-turbo"):
    encoder = tiktoken.encoding_for_model(model_name)

    file_input_tokens = []
    file_output_tokens = []
    matched_tokens = []
    unmatched_tokens = []

    # Read fixed_so_far file
    with open(fixed_file_path, "r", encoding="utf-8") as fixed_file:
        fixed_strings = [line.strip().replace(" ", "_") for line in fixed_file]

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
            continue

        input_tokens_sum = 0
        output_tokens_sum = 0

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # Split the content into ChatSequences
        chat_sequences = re.split(r"={15,}\s*", content)

        for sequence in chat_sequences:
            if not sequence.strip():
                continue

            # Extract input tokens
            input_tokens_match = re.search(r"Length:\s*(\d+)\s*tokens", sequence)
            if input_tokens_match:
                input_tokens = int(input_tokens_match.group(1))
                input_tokens_sum += input_tokens

            # Extract ASSISTANT to USER text
            assistant_match = re.search(r"--------------- ASSISTANT ----------------(.*?)(?=------------------ USER ----------------|$)", sequence, re.DOTALL)
            if assistant_match:
                assistant_text = assistant_match.group(1).strip()
                output_tokens_sum += len(encoder.encode(assistant_text))

        total_tokens = input_tokens_sum + output_tokens_sum
        file_input_tokens.append(input_tokens_sum)
        file_output_tokens.append(output_tokens_sum)

        # Check if the filename matches any fixed string
        matched = any(fixed_string in filename for fixed_string in fixed_strings)
        if matched:
            matched_tokens.append(total_tokens)
        else:
            unmatched_tokens.append(total_tokens)

    total_input_tokens = sum(file_input_tokens)
    total_output_tokens = sum(file_output_tokens)

    average_input_tokens = statistics.mean(file_input_tokens) if file_input_tokens else 0
    average_output_tokens = statistics.mean(file_output_tokens) if file_output_tokens else 0

    median_input_tokens = statistics.median(file_input_tokens) if file_input_tokens else 0
    median_output_tokens = statistics.median(file_output_tokens) if file_output_tokens else 0

    # Statistics for matched and unmatched files
    average_matched_tokens = statistics.mean(matched_tokens) if matched_tokens else 0
    median_matched_tokens = statistics.median(matched_tokens) if matched_tokens else 0

    average_unmatched_tokens = statistics.mean(unmatched_tokens) if unmatched_tokens else 0
    median_unmatched_tokens = statistics.median(unmatched_tokens) if unmatched_tokens else 0

    # Create violin plot
    categories = ["All Files", "Matched Files", "Unmatched Files"]
    data = [[i+j for i, j in zip(file_input_tokens, file_output_tokens)], matched_tokens, unmatched_tokens]

    plt.figure(figsize=(10, 6))
    plt.violinplot(data, showmeans=True)
    plt.xticks(range(1, len(categories) + 1), categories)
    plt.title("Token Distribution Across File Categories")
    plt.ylabel("Number of Tokens (Input + Output)")
    plt.grid(axis="y")
    plt.show()

    return (total_input_tokens, total_output_tokens, 
            average_input_tokens, average_output_tokens, 
            median_input_tokens, median_output_tokens, 
            average_matched_tokens, median_matched_tokens,
            average_unmatched_tokens, median_unmatched_tokens, data)

if __name__ == "__main__":
    folder_path = "prompt_logs"  # Replace with the path to your folder
    fixed_file_path = "fixed_so_far"  # Replace with the path to your fixed_so_far file

    if not os.path.exists(folder_path):
        print(f"Error: The folder '{folder_path}' does not exist.")
    elif not os.path.exists(fixed_file_path):
        print(f"Error: The file '{fixed_file_path}' does not exist.")
    else:
        (input_tokens_sum, output_tokens_sum, 
         avg_input_tokens, avg_output_tokens, 
         med_input_tokens, med_output_tokens,
         avg_matched_tokens, med_matched_tokens,
         avg_unmatched_tokens, med_unmatched_tokens, data) = calculate_tokens(folder_path, fixed_file_path)

        print(f"Total Input Tokens: {input_tokens_sum}")
        print(f"Total Output Tokens: {output_tokens_sum}")
        print(f"Average Input Tokens Per File: {avg_input_tokens}")
        print(f"Average Output Tokens Per File: {avg_output_tokens}")
        print(f"Median Input Tokens Per File: {med_input_tokens}")
        print(f"Median Output Tokens Per File: {med_output_tokens}")

        print(f"Average Tokens for Matched Files: {avg_matched_tokens}")
        print(f"Median Tokens for Matched Files: {med_matched_tokens}")

        print(f"Average Tokens for Unmatched Files: {avg_unmatched_tokens}")
        print(f"Median Tokens for Unmatched Files: {med_unmatched_tokens}")
        import matplotlib.pyplot as plt
        import seaborn as sns
        import pandas as pd

        # Example data structure
        #data = [int(i/1000) for i in data]
        data = {
            "Category": ["Unfixed bugs"] * len(data[2]) + ["Fixed bugs"] * len(data[1]) + ["All"] * len(data[0]),
            "Tokens":  [int(i/1000) for i in data[2]] + [int(i/1000) for i in data[1]] + [int(i/1000) for i in data[0]],
        }

        df = pd.DataFrame(data)
        # Create a DataFrame
        fig, ax = plt.subplots(figsize=(8, 6))

        # Create the violin plot
        sns.violinplot(x="Category", y="Tokens", data=df, palette="muted", inner="box", ax=ax)

        # Add horizontal grid lines (matches the style in the original plot)
        ax.yaxis.grid(True)  # Enable horizontal grid lines
        ax.grid(which='major', linestyle='-', linewidth=0.5, color='gray')  # Style for major grid lines
        ax.grid(which='minor', linestyle='--', linewidth=0.3, color='lightgray')  # Style for minor grid lines

        # Customize the y-axis label
        ax.set_ylabel("Count of tokens per bug (K)")
        ax.set_xlabel("")

        # Add a second y-axis for cost (simulating dual y-axis in the original plot)
        ax2 = ax.twinx()
        ax2.set_ylabel("Cost of Querying GPT3.5 per bug in USD")

        # Set the secondary y-axis limits to align with primary axis
        ax2.set_ylim(ax.get_ylim()[0] * 0.0005, ax.get_ylim()[1] * 0.0005)  # Scale for cost (example)

        # Show the plot
        plt.show()