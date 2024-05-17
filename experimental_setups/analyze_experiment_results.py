import os
from prettytable import PrettyTable
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas

all_correctly_fixed = []
detailed_fixed_main = []
def count_suggested_fixes(log_content):
    chat_sequences = log_content.split("============== ChatSequence ==============")
    last_sequence = chat_sequences[-1]
    num_suggested_fixes = last_sequence.count("###Fix:")
    return num_suggested_fixes

def analyze_experiment(experiment_folder):
    logs_folder = os.path.join(experiment_folder, 'logs')
    log_files = [f for f in os.listdir(logs_folder) if os.path.isfile(os.path.join(logs_folder, f))]
    num_log_files = len(log_files)

    table = PrettyTable()
    table.field_names = ["Log File", "Correctly Fixed", "Suggested Fixes", "Number of Queries"]
    table.align["Log File"] = "l"

    correctly_fixed_bugs = 0
    total_suggested_fixes = 0
    total_queries = 0
    all_suggested_fixes = []

    for log_file in log_files:
        log_file_path = os.path.join(logs_folder, log_file)
        with open(log_file_path, 'r') as file:
            log_content = file.read()

            # Counting queries
            num_queries = log_content.count("============== ChatSequence ==============")
            total_queries += num_queries

            is_correctly_fixed = ' 0 failing test' in log_content
            if is_correctly_fixed:
                correctly_fixed_bugs += 1

            num_suggested_fixes = count_suggested_fixes(log_content)
            total_suggested_fixes += num_suggested_fixes

            # Extract suggested fixes
            chat_sequences = log_content.split("============== ChatSequence ==============")
            last_sequence = chat_sequences[-1]
            suggested_fixes_start = last_sequence.find("## Suggested fixes:") + len("## Suggested fixes:")
            suggested_fixes_end = last_sequence.find("## Executed search queries within the code base:")
            suggested_fixes_text = last_sequence[suggested_fixes_start:suggested_fixes_end].strip()
            all_suggested_fixes.append((log_file.replace("prompt_history_",""), suggested_fixes_text))

            # Add rows to the table without color
            table.add_row([log_file.replace("prompt_history_", ""), "Yes" if is_correctly_fixed else "No", num_suggested_fixes, num_queries])
            if is_correctly_fixed:
                all_correctly_fixed.append(log_file.replace("prompt_history_", "").replace("_", " "))
                detailed_fixed_main.append(experiment_folder + " " + log_file.replace("prompt_history_", "").replace("_", " "))
    return num_log_files, table, correctly_fixed_bugs, total_suggested_fixes, total_queries, all_suggested_fixes


def generate_pdf(experiment_folder, num_log_files, table, correctly_fixed_bugs, total_suggested_fixes):
    pdf_filename = f"{experiment_folder}_results.pdf"

    # Create a PDF document
    pdf = canvas.Canvas(pdf_filename, pagesize=A4)

    pdf.setFont("Helvetica", 16)
    pdf.drawString(100, 800, f"{experiment_folder}")

    # Add content to the PDF
    pdf.setFont("Helvetica", 12)
    #pdf.drawString(100, 700, f"Experiment: {experiment_folder}")
    pdf.drawString(100, 680, f"Number of log files: {num_log_files}")
    pdf.drawString(100, 660, f"Correctly fixed bugs: {correctly_fixed_bugs}")
    pdf.drawString(100, 640, f"Total Suggested Fixes: {total_suggested_fixes}")

    # Draw the table
    table_data = [table.field_names] + table._rows
    col_widths = [pdf.stringWidth(str(max(col, key=lambda x: len(str(x)))).strip(), "Helvetica", 10) + 30 for col in zip(*table_data)]
    row_height = 12

    x = 100
    y = 600

    for row in table_data:
        for i, cell in enumerate(row):
            pdf.drawString(x, y, str(cell))
            x += col_widths[i]
        x = 100
        y -= row_height

    # Save the PDF
    pdf.save()

    print(f"Results saved to {pdf_filename}")

def write_to_text_file(experiment_folder, num_log_files, table, correctly_fixed_bugs, total_suggested_fixes, all_suggested_fixes):
    text_filename = f"{experiment_folder}_results.txt"

    with open(text_filename, 'w') as text_file:
        # Write title to the text file
        text_file.write(f"Experiment Results: {experiment_folder}\n\n")

        # Write content to the text file
        text_file.write(f"Number of Bugs: {num_log_files}\n")
        text_file.write(f"Correctly fixed bugs: {correctly_fixed_bugs}\n")
        text_file.write(f"Total Suggested Fixes: {total_suggested_fixes}\n\n")
        sgf = '\n\n'.join("\n".join([a, b]) for a, b in all_suggested_fixes).replace(
            "This is the list of suggested fixes so far but none of them worked:", "").replace(
            "No fixes were suggested yet.", ""
            )
        text_file.write(f"The list of suggested fixes:\n{sgf}\n\n")
        # Write the table
        for row in table.get_string().split('\n'):
            text_file.write(row + '\n')

    print(f"Results saved to {text_filename}")

def main():
    with open('experiments_list.txt', 'r') as experiments_list_file:
        experiment_folders = experiments_list_file.read().splitlines()

    total_correctly_fixed_bugs = 0
    total_suggested_fixes = 0

    for experiment_folder in experiment_folders:
        num_log_files, table, correctly_fixed_bugs, suggested_fixes, total_queries, all_suggested_fixes = analyze_experiment(experiment_folder)

        #print(f"Experiment: {experiment_folder}")
        #print(f"Number of log files: {num_log_files}")
        #print(f"List of log files:")
        #print(table)
        #print(f"Correctly fixed bugs: {correctly_fixed_bugs}")
        #print(f"Total Suggested Fixes: {suggested_fixes}")
        #print(f"Total Queries: {total_queries}")
        #print(f"List of Suggested Fixes:")
        for idx, suggested_fixes_text in enumerate(all_suggested_fixes, 1):
            pass
            #print(f"\nSuggested Fixes in Log File {idx}:\n{suggested_fixes_text}\n")

        #generate_pdf(experiment_folder, num_log_files, table, correctly_fixed_bugs, suggested_fixes, total_queries)
        write_to_text_file(experiment_folder, num_log_files, table, correctly_fixed_bugs, suggested_fixes, all_suggested_fixes)


    #print(f"Total Correctly Fixed Bugs Across Experiments: {total_correctly_fixed_bugs}")
    #print(f"Grand Total Suggested Fixes Across Experiments: {total_suggested_fixes}")

if __name__ == "__main__":
    main()
    print(len(set(all_correctly_fixed)))
    print("\n".join(list(set(all_correctly_fixed))))
    with open("fixed_so_far") as fsf:
        fixed_so_far = fsf.read().splitlines()

    fixed_so_far += all_correctly_fixed

    with open("fixed_so_far", "w") as fsf:
        fsf.write("\n".join(list(set(fixed_so_far))))

    with open("detailed_fixed_main", "w") as dfm:
        dfm.write("\n".join(list(set(detailed_fixed_main)))) 