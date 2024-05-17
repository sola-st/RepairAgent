import os


detailed_fully_executed = []

def extract_project_bug(log_file):
    parts = log_file.split("_")
    project_name = parts[-2]
    bug_number = parts[-1]
    return project_name, bug_number

def analyze_experiment(experiment_folder, output_file):
    logs_folder = os.path.join(experiment_folder, 'logs')
    log_files = [f for f in os.listdir(logs_folder) if os.path.isfile(os.path.join(logs_folder, f))]

    for log_file in log_files:
        log_file_path = os.path.join(logs_folder, log_file)
        with open(log_file_path, 'r') as file:
            log_content = file.read()

            # Counting queries
            num_queries = log_content.count("============== ChatSequence ==============")
            if num_queries >= 38: ## can be changed
                project_name, bug_number = extract_project_bug(log_file)
                detailed_fully_executed.append((experiment_folder, project_name, bug_number))
                output_file.write(f"{project_name} {bug_number}\n")

def main():
    with open('experiments_list.txt', 'r') as experiments_list_file:
        experiment_folders = experiments_list_file.read().splitlines()

    with open('pairs_output.txt', 'w') as output_file:
        for experiment_folder in experiment_folders:
            experiment_number = int(experiment_folder.split("_")[1])
            if experiment_number > 0: ## can be changed
                analyze_experiment(experiment_folder, output_file)

    print("Pairs written to pairs_output.txt")

if __name__ == "__main__":
    main()
    with open("detailed_fully_executed", "w") as dfe:
        dfe.write("\n".join([" ".join(c) for c in detailed_fully_executed]))