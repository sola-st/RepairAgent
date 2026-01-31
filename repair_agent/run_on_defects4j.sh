#!/bin/bash
export PATH=$PATH:$(pwd)/defects4j/framework/bin
cpanm --local-lib=~/perl5 local::lib && eval $(perl -I ~/perl5/lib/perl5/ -Mlocal::lib)
for LANG in en_AU.UTF-8 en_GB.UTF-8 C.UTF-8 C; do
  if locale -a 2>/dev/null | grep -q "$LANG"; then
    export LANG
    break
  fi
done
export LC_COLLATE=C

"""
Replication_Modification: Outputs to Individual Bug Directory
Originally, every run of run_on_defects4j.sh would create a new experiment_* directory with subdirectories. Then for every bug, 
autogpt/agents/base.py and autogpt/agents/agent.py would output artifacts to the appropriate subdirectory. This is unweildy for 
a Kubernetes implementation where bugs are run concurrently because it can create a race condition on the experiments_list.txt.  
Now, the folder experiment_1 is mounted as a PVC to each bug pod and the job creates a bug-specific directory. 
Commenting out the increment_experiment.py script, will prevent every execution of run_on_defects4j.sh from creating 
a new experiment directory for each and every bug.
"""
# python3 experimental_setups/increment_experiment.py
python3 construct_commands_descriptions.py

input="$1"
experiment_file="$2"
model="${3:-gpt-4o-mini}"  # Use $3 if given, otherwise default to gpt-4o-mini

dos2unix "$input"  # Convert file to Unix line endings (if needed)

while IFS= read -r line || [ -n "$line" ]
do
    tuple=($line)
    echo ${tuple[0]}, ${tuple[1]}
    python3 prepare_ai_settings.py "${tuple[0]}" "${tuple[1]}"
    python3 checkout_py.py "${tuple[0]}" "${tuple[1]}"
    ./run.sh --ai-settings ai_settings.yaml --model "$model" -c -l 40 -m json_file --experiment-file "$experiment_file"
done < "$input"
