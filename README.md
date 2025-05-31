# 🛠️ RepairAgent

RepairAgent is an autonomous LLM-based agent designed for automated program repair. For a comprehensive understanding of its workings and development, you can check out our [research paper here](https://arxiv.org/abs/2403.17134).

---

## 🚨✨ **UPDATE – June 2025** ✨🚨

> **⚡ The script now supports multiple AI models!**
>
> You can now specify the model using a command-line argument:
>
> ```bash
> bash your_script.sh <input.txt> <params.json> <model-name>
> ```
> See below for detailed instructions.
> If `<model-name>` is omitted, the script will use the default: `gpt-4o-mini`.

**Supported Models:**
- `gpt-4o-mini` (default)
- `gpt-4.1`
- `gpt-4o`
- `gpt-4.1-mini`
- `gpt-4.1-nano`

> ⚠️ **Don't forget to update your command usage!**


## 📋 I. Requirements

Before you start using RepairAgent, ensure that your system meets the following requirements:

- **Docker**: Version 20.04 or higher. For installation instructions, see the [Docker documentation](https://docs.docker.com/get-docker).
- **VS Code**: Not a hard requirement but highly recommended. VS Code provides an easy way to interact with RepairAgent using Dev Containers (see the instructions below).
- **OpenAI Token and Credits**:
  - Create an account on the OpenAI website and purchase credits to use the API.
  - Generate an API token on the same website.
- **Disk Space**:
    - At least 40GB of available disk space on your machine. The code itself does not take 40GB. However, the dependencies might take up to 8GB, and files generated from running on different instances may use more. 40GB is a safe estimate.
    - If you are using VS Code Dev Containers, you can avoid pulling the heavy Docker image (~22GB).
- **Internet Access**: Required while running RepairAgent to connect to OpenAI's API.

---

## ⚙️ II. How to Use RepairAgent?

You have two ways to use RepairAgent:

1. **Start a VS Code Dev Containers**: The easiest method, as it avoids pulling the large Docker image.
2. **Use the Docker Image**: Suitable for users familiar with Docker.

### 🚀 Option 1: Using a VS Code Dev Containers

### **STEP 1: Open RepairAgent in a Dev Containers**

1. Ensure you have the **Dev Containers** extension installed in VS Code. You can install it from the [Visual Studio Code Marketplace](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

2. Clone the RepairAgent repository:

   ```bash
   git clone https://github.com/sola-st/RepairAgent.git
   cd RepairAgent
   cd repair_agent
   rm -rf defects4j
   git clone https://github.com/rjust/defects4j.git
   cp -r ../data/buggy-lines defects4j
   cp -r ../data/buggy-methods defects4j
   cd ../..
   ```

3. Open the repository folder in VS Code.

4. When prompted by VS Code to "Reopen in Container," click it. If not prompted, open the Command Palette (Ctrl+Shift+P) and select "Dev Containers: Reopen in Container." VS Code will now build and start the DevContainer, setting up the environment for you.

5. Within your VS Code terminal, move to the folder repair_agent
    ```bash
    cd repair_agent
    ```

6. Update Git indices to assume unchanged for the to-be-modified files, to avoid submitting these files accidentally:
    ```bash
    # Will be modified when setting the OpenAI API key
    git update-index --assume-unchanged .env
    git update-index --assume-unchanged autogpt/.env
    git update-index --assume-unchanged autogpt/commands/defects4j.py
    git update-index --assume-unchanged autogpt/commands/defects4j_static.py
    git update-index --assume-unchanged run.sh

    # Will be modified when running the experiments
    git update-index --assume-unchanged ai_settings.yaml
    git update-index --assume-unchanged defects4j
    git update-index --assume-unchanged experimental_setups/bugs_list
    git update-index --assume-unchanged experimental_setups/experiments_list.txt
    git update-index --assume-unchanged experimental_setups/fixed_so_far
    git update-index --assume-unchanged model_logging_temp.txt
    ```

### **STEP 2: Set the OpenAI API Key**

Inside the DevContainer terminal, configure your OpenAI API key by running:

```bash
python3.10 set_api_key.py
```

The script will prompt you to paste your API token.

### **STEP 3: Start RepairAgent**

By default, RepairAgent is configured to run on Defects4J bugs. To specify which bugs to run on:

1. Create a text file named, for example, `bugs_list`. A sample file exists in the repository at `experimental_setups/bugs_list`.
2. Run the following command:

   ```bash
   ./run_on_defects4j.sh experimental_setups/bugs_list hyperparams.json gpt-4o-mini
   ```

You can open the `hyperparams.json` file to review or customize its parameters (explained further in the customization section).


**If you went with this option, you can jump to section `4.1 What Happens When You Start RepairAgent?` to see more details on the results of running RepairAgent.**

---

### 🚀 Option 2: Using the Docker Image

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
- Attach the container to a new window by clicking the "+" sign to the right of the container name, then navigate to the `workdir` folder in the VS Code window (**the workdir is `/app/AutoGPT`**).
- **Tutorial Reference**: For detailed steps on attaching a Docker container in VS Code, check out this [video tutorial (1min 38 sec)](https://www.youtube.com/watch?v=8gUtN5j4QnY&t).

### **STEP 3: Set the OpenAI API Key**

Inside the Docker container, configure your OpenAI API key by running:

```bash
python3.10 set_api_key.py
```

The script will prompt you to paste your API token.

### **STEP 4: Start RepairAgent**

By default, RepairAgent is configured to run on Defects4J bugs. To specify which bugs to run on:

1. Create a text file named, for example, `bugs_list`. A sample file exists in the repository and Docker image at `experimental_setups/bugs_list`.
2. Run the following command:

   ```bash
   ./run_on_defects4j.sh experimental_setups/bugs_list hyperparams.json gpt-4o-mini
   ```

You can open the `hyperparams.json` file to review or customize its parameters (explained further in the customization section).

#### **4.1 What Happens When You Start RepairAgent?**

- RepairAgent checks out the project with the given bug ID.
- It initiates the autonomous repair process.
- Logs detailing each step performed will be displayed in your terminal.

#### **4.2 Retrieve Repair Logs and History**

RepairAgent saves the output in multiple files.

- The primary logs are located in the folder `experimental_setups/experiment_X`, where `experiment_X` increments automatically with each run of the command `./run_on_defects_4j.sh`.

- Within this folder, you may find several subfolders:
  - **logs**: Full chat history (prompts) and command outputs (one file per bug).
  - **plausible_patches**: Any plausible patches generated (one file per bug).
  - **mutations_history**: Suggested fixes derived by mutating prior suggestions (one file per bug).
  - **responses**: Responses from the agent (LLM) at each cycle (one file per bug).

#### **4.3 Analyze Logs**

Within the `experimental_setups` folder, several scripts are available to post-process the logs:

- **Collect Plausible Patches**:
  Use the script `collect_plausible_patches_files.py` to gather the generated plausible patches across multiple experiments:
  
  ```bash
  python3.10 collect_plausible_patches_files.py 1 10
  ```
  
  `A plausible patch is a patch that passes all test cases and is a candidate to be the correct patch`

- **Get Fully Executed Runs**:
  Use `get_list_of_fully_executed.py` to retrieve runs that reached at least 38 out of 40 cycles. This allows to identify executions that terminated unexpectedly or called the exit function prematurely.

  ```bash
  python3.10 get_list_of_fully_executed.py
  ```

- **Analyze experiments results**:
  Produces a summary for all executed experiments so far. A text file is generated for each experiment where it shows all the suggested patches per bug and also a table with BugID, number of cycles, number of suggested patches and the number of plausible patches.

  ```bash
  python3.10 analyze_experiment_results.py
  ```

  An example of the output file would look like this:
  ```md
  Experiment Results: experiment_60

  Number of Bugs: 2
  Correctly fixed bugs: 1
  Total Suggested Fixes: 4

  The list of suggested fixes:
  Cli_8

  ###Fix:
  Lines:['812', '813', '814', '815', '816', '817', '818', '819', '820'] from file /workspace/Auto-GPT/auto_gpt_workspace/cli_8_buggy/src/java/org/apache/commons/cli/HelpFormatter.java were replaced with the following:
  {'812': 'pos = findWrapPos(text, width, 0);', '813': 'if (pos == -1) { sb.append(rtrim(text)); return sb; }', '814': 'sb.append(rtrim(text.substring(0, pos))).append(defaultNewLine);', '815': 'final String padding = createPadding(nextLineTabStop);', '816': 'while (true) {', '817': 'text = padding + text.substring(pos).trim();', '818': 'pos = findWrapPos(text, width, nextLineTabStop);', '819': 'if (pos == -1) { sb.append(text); return sb; }', '820': 'sb.append(rtrim(text.substring(0, pos))).append(defaultNewLine);'}

  ###Fix:
  Lines:['812', '813', '814', '815', '816', '817', '818', '819', '820'] from file /workspace/Auto-GPT/auto_gpt_workspace/cli_8_buggy/src/java/org/apache/commons/cli/HelpFormatter.java were replaced with the following:
  {'812': 'pos = findWrapPos(text, width, nextLineTabStop);', '813': 'if (pos == -1) { sb.append(rtrim(text)); return sb; }', '814': 'sb.append(rtrim(text.substring(0, pos))).append(defaultNewLine);', '815': 'final String padding = createPadding(nextLineTabStop);', '816': 'while (true) {', '817': 'text = padding + text.substring(pos).trim();', '818': 'pos = findWrapPos(text, width, nextLineTabStop);', '819': 'if (pos == -1) { sb.append(text); return sb; }', '820': 'sb.append(rtrim(text.substring(0, pos))).append(defaultNewLine);'}

  ###Fix:
  Lines:['812', '813', '814', '815', '816', '817', '818', '819', '820'] from file /workspace/Auto-GPT/auto_gpt_workspace/cli_8_buggy/src/java/org/apache/commons/cli/HelpFormatter.java were replaced with the following:
  {'812': 'pos = findWrapPos(text, width, nextLineTabStop);', '813': 'if (pos == -1) { sb.append(rtrim(text)); return sb; }', '814': 'sb.append(rtrim(text.substring(0, pos))).append(defaultNewLine);', '815': 'final String padding = createPadding(nextLineTabStop);', '816': 'while (true) {', '817': 'text = padding + text.substring(pos).trim();', '818': 'pos = findWrapPos(text, width, nextLineTabStop);', '819': 'if (pos == -1) { sb.append(text); return sb; }', '820': 'sb.append(rtrim(text.substring(0, pos))).append(defaultNewLine);'}

  Chart_1

  ###Fix:
  Lines:['1797'] from file org/jfree/chart/renderer/category/AbstractCategoryItemRenderer.java were replaced with the following:
  {'1797': 'if (dataset == null) {'}

  +----------+-----------------+-----------------+-------------------+
  | Log File | Correctly Fixed | Suggested Fixes | Number of Queries |
  +----------+-----------------+-----------------+-------------------+
  | Cli_8    |        No       |        3        |         32        |
  | Chart_1  |       Yes       |        1        |         10        |
  +----------+-----------------+-----------------+-------------------+

  ```
---

## ✨ III. Customize RepairAgent

### 1. Modify `hyperparams.json`

- **Budget Control Strategy**: Defines how the agent views the remaining cycles, suggested fixes, and minimum required fixes:
  - **FULL-TRACK**: Put the max, consumed and left budget in the prompt (default for our experiments).
  - **NO-TRACK**: Suppresses budget information.
  - **FORCED**: Experimental and buggy—avoid use (we did not use this option).
  
  Example Configuration:
  
  ```json
  "budget_control": {
      "name": "FULL-TRACK",
      "params": {
          "#fixes": 4 //The agent should suggest at least 4 patches within the given budget, the number is updated based on agent progress (4 is default).
      }
  }
  ```

- **Repetition Handling**: Default settings restrict repetitions.
  ```json
  "repetition_handling": "RESTRICT",
  ```

- **Command Limit**: Controls the maximum allowed cycles (budget).
  ```json
  "commands_limit": 40 // default for our experiment
  ```

- **Request External Fixes**: Experimental feature allowing the request of fixes from another LLM.
  ```json
  "external_fix_strategy": 0, // deafult for our experiment
  ```

### 2. Switch Between GPT-3.5 and GPT-4

In the `run_on_defects4j.sh` file, locate the line:
```bash
./run.sh --ai-settings ai_settings.yaml --gpt3only -c -l 40 -m json_file --experiment-file "$2"
```
- The `--gpt3only` flag enforces GPT-3.5 usage. Removing this flag switches RepairAgent to GPT-4.
- Search the codebase for "gpt-3" and "gpt-4" to update version names accordingly.

---

## 📊 IV. Our Data

In our experiments, we utilized RepairAgent on the Defects4J dataset, successfully fixing 164 bugs. You can check our data under the folder data.
- The list of fixed bugs [here](./data/final_list_of_fixed_bugs). The list allows to compare with prior and future work.
  * For example, we compare to ChatRepair, SelfAPR, and ITER. The venn diagram of Figure 6 is produced using the command:
    ```bash
    python3.10 draw_venn_chatrepair_clean.py
    ```
  * The file [d4j12.csv](./repair_agent/experimental_setups/d4j12.csv) contains the list of bugs fixed by previous work. The script draw_venn_chatrepair_clean.py contains the list of fixes that we compare to.
- The implementation details of the patches in [this file](./data/fixes_implementation).
 
- The folder **data/root_patches** contains patches produced by RepairAgent in the main phase
- The folder **data/derivated_pathces** contains patches obtained by mutating **root_patches**


Note: RepairAgent encountered exceptions due to Middleware errors in 29 bugs, which were not re-run.

---

## 🧫 V. Replicate Experiments
This part is about running RepairAgent on full evaluation datasets to replicate our experiments. The process is the same as above; We just provide ready-to-use input files and instructions for replication.

### Replicate Defects4J experiments
1. Create the execution batches for Defects4J which will create lists of bugs to run on.
    ```bash
    python3.10 get_defects4j_list.py
    ```
    The result of this command can be found in `experimental_setups/batches`

2. Run RepairAgent on each of the batches (either singularly or concurrently)
    ```bash
    ./run_on_defects4j.sh experimental_setups/batches/0 hyperparameters.json
    # replace 0 with the desired batch number
    ```

3. Refer to sections `4.2 Retrieve Repair Logs and History` and `4.3 Analyze Logs` on how to analyze logs and summarize the results of the experiments.

4. Furthermore, you can adapt the script `experimental_setups/generate_main_table.py` to generate the main comparative table (Table III in the paper)
   - 4.1. You can also use `experimental_setups/draw_venn_chatrepair_clean.py` to draw a venn diagram to compare different techniques (Figure 6 of the paper)  
5. You can use the script `experimental_setups/calculate_tokens.py` to calculate the costs of the agent (used to generate figure 9).

6. You can use the script `experimental_setups/collect_plausible_patches_files.py` to get the list of plausible patches to inspect.


### Replicate GitBugsJava Experiment
GitBugsJava is another dataset for program repair evaluation.
 
 1. First,prepare the GitBugsJava VM. Since this dataset requires a heavy VM (at least 140 GB of disk), we could not include it in this artifact. We added more detailed instruction on how to prepare such VM. Please check the step by step process here: https://github.com/gitbugactions/gitbug-java

 2. Copy the repository of RepairAgent inside the VM.

 3. Run RepairAgent on the list of bugs by specifying the file `experimental_setups/gitbuglist` as the target file.

 4. Use the same analysis scripts as part 1 (D4j replication) to analyse the results of the experiments.

## 💬 VI. Help Us Improve RepairAgent

If you use RepairAgent, we encourage you to report any issues, bugs, or documentation gaps. We are committed to addressing your concerns promptly.

You can raise an issue directly in this repository, or for any queries, feel free to [email me](mailto:fi_bouzenia@esi.dz).

--- 