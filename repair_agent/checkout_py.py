import subprocess
import os
import argparse

def checkout_project(project_name, version):
    write_to = os.path.join("auto_gpt_workspace", "{}_{}_buggy".format(project_name.lower(), version))
    command = f'defects4j checkout -p {project_name} -v {version}b -w {write_to}'

    # Execute the command
    try:
        subprocess.run(command, shell=True, check=True)
        print("Checkout completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Checkout failed with error: {e}")


parser = argparse.ArgumentParser()
parser.add_argument("project")
parser.add_argument("index")
args = parser.parse_args()

checkout_project(args.project, args.index)
