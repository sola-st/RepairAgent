# 🛠️ RepairAgent

RepairAgent is an autonomous LLM-based agent designed for automated program repair. For a comprehensive understanding of its workings and development, you can check out our [research paper here](https://arxiv.org/abs/2403.17134).

---

## 📋 I. Requirements

Before you start using RepairAgent, ensure that your system meets the following requirements:

- **Docker**: Version 20.04 or higher. For installation instructions, see the [Docker documentation](https://docs.docker.com/get-docker).
- **OpenAI Token and Credits**:
  - Create an account on the OpenAI website and purchase credits to use the API.
  - Generate an API token on the same website.
- **Disk Space**: At least 40GB of available disk space on your machine.
- **Internet Access**: Required while running RepairAgent to connect to OpenAI's API.

---

## ⚙️ II. How to Use RepairAgent?

To use RepairAgent, the easiest method is to pull a ready-to-use Docker image from DockerHub. Using the Docker image ensures that RepairAgent is pre-installed, and all you need to do is provide your OpenAI API key.

### 🚀 Steps to Get Started:

### **STEP 1: Pull the Docker Image**

Run the following commands in your terminal to retrieve and start our Docker image:

```bash
# Pull the image from DockerHub
docker pull islemdockerdev/repair-agent:v1

# Run the image inside a container
docker run -itd --name apr-agent islemdockerdev/repair-agent:v1

# Start the container
docker start -i apr-agent
```

### **STEP 2: Attach the Container to VS Code**

- After starting the container, open VS Code and navigate to the **Containers** icon on the left panel. Ensure you have the **Remote Explorer** extension installed.
- Under the **Dev Containers** tab, find the name of the container you just started (e.g., `apr-agent`).
- Attach the container to a new window by clicking the '+' sign to the right of the container name, then navigate to the `workdir` folder in the VS Code window (**the workdir is `/app/AutoGPT`**).
- **Tutorial Reference**: For detailed steps on attaching a Docker container in VS Code, check out this [video tutorial (1min 38 sec)](https://www.youtube.com/watch?v=8gUtN5j4QnY&t).

### **STEP 3: Set the OpenAI API Key**

RepairAgent relies on OpenAI's LLMs (like GPT-3.5). To configure it, obtain your OpenAI API key and execute the following command within the Docker container:

```bash
python3.10 set_api_key.py
```

The script will prompt you to paste your API token.

### **STEP 4: Start RepairAgent**

By default, RepairAgent is configured to run on Defects4J bugs. 

- To specify which bugs to run on, create a text file named, for example, `bugs_list`. A sample file exists in the repository and Docker image at the location `experimental_setups/bugs_list`.
  
Once created, execute the following command:

```bash
./run_on_defects4j.sh experimental_setups/bugs_list hyperparameters.json
```

You can open the `hyperparameters.json` file to check its parameters (explained more in the customization section).

#### **4.1 What Happens When You Start RepairAgent?**

- RepairAgent checks out the project with the given bug ID.
- It initiates the autonomous repair process.
- Logs detailing each step performed will be displayed in your terminal.

#### **4.2 Retrieve Repair Logs and History**

RepairAgent saves the output in multiple files.

- The primary logs are located in the folder `experimental_setups/experiment_X`, where `experiment_X` increments automatically with each run of the command `run_on_defects_4j`.

- Within this folder, you may find several subfolders:
  - **logs**: Full chat history (prompts) and command outputs (one file per bug).
  - **plausible_patches**: Any plausible patches generated (one file per bug).
  - **mutations_history**: Suggested fixes derived by mutating prior suggestions (one file per bug).
  - **responses**: Responses from the agent at each cycle (one file per bug).

#### **4.3 Analyze Logs**

Within the `experimental_setups` folder, several scripts are available to post-process the logs:

- **Collect Plausible Patches**:
  Use the script `collect_plausible_patches_files.py` to gather the generated plausible patches across multiple experiments:
  
  ```bash
  python3.10 experimental_setups/collect_plausible_patches_files.py 1 10
  ```
  
  This script collects both mutation-based patches from the `plausible_patches` directory and external fixes from the `external_fixes` directory. External fixes will be prefixed with `[External]` in the output list and `external_` in the filename.

- **Get Fully Executed Runs**:
  Utilize `get_list_of_fully_executed.py` to retrieve runs that reached at least 38 out of 40 cycles. This identifies executions that terminated unexpectedly or called the exit function prematurely.

---

## ✨ III. Customize RepairAgent

### 1. Modify `hyperparams.json`

- **Budget Control Strategy**: Defines how the agent views the remaining cycles, suggested fixes, and minimum required fixes:
  - **FULL-TRACK**: Displays full budget information.
  - **NO-TRACK**: Suppresses budget information.
  - **FORCED**: Experimental and buggy—avoid use.
  
  Example Configuration:
  
  ```json
  "budget_control": {
      "name": "FULL-TRACK",
      "params": {
          "#fixes": 4
      }
  }
  ```

- **Repetition Handling**: Default settings restrict repetitions.
  ```json
  "repetition_handling": "RESTRICT",
  ```

- **Command Limit**: Controls the maximum allowed cycles.
  ```json
  "commands_limit": 40
  ```

- **Request External Fixes**: Experimental feature allowing the request of fixes from another LLM.
  ```json
  "external_fix_strategy": 0,
  ```

### 2. Switch Between GPT-3.5 and GPT-4

In the `run_on_defects4j.sh` file, locate the line:
```bash
./run.sh --ai-settings ai_settings.yaml --gpt3only -c -l 40 -m json_file --experiment-file "$2"
```
- The `--gpt3only` flag enforces GPT-3.5 usage. Removing this flag switches RepairAgent to GPT-4.
- Search the codebase for "gpt-3" and "gpt-4" to update version names accordingly.

### 3. Run RepairAgent on an Arbitrary Project

Documentation for this feature is forthcoming in version 0.7.0. We are working on simplifying this process into a single command for ease of use.

---

## 🔧 IV. Our Patches

In our experiments, we utilized RepairAgent on the Defects4J dataset, successfully fixing 164 bugs. You can view:
- The list of fixed bugs [here](./final_list_of_fixed_bugs).
- The implementation details of the patches in [this file](./fixes_implementation).

Note: RepairAgent encountered exceptions due to Middleware errors in 29 bugs, which were not re-run.

---

## 💬 V. Help Us Improve RepairAgent

If you use RepairAgent, we encourage you to report any issues, bugs, or documentation gaps. We are committed to addressing your concerns promptly.

You can raise an issue directly in this repository, or for any queries, feel free to [email me](mailto:fi_bouzenia@esi.dz).

--- 

Thank you for your interest in RepairAgent! Happy bug fixing! 🐞✨