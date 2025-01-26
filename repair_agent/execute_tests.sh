#!/bin/bash

# Check if argument is provided
if [ $# -ne 1 ]; then
    echo "Usage: $0 <PATH>"
    exit 1
fi

# Navigate to the directory
cd /home/ubuntu/gitbug-java || exit

# Activate the virtual environment
source .venv/bin/activate

#export PATH="$(pwd):$(pwd)/bin:$PATH"

echo $PATH

pwd

echo $1
# Run gitbug-java with the provided PATH argument
cp -r $1 temp_folder_cache
gitbug-java run $1 > test_results_temp

rm -rf $1

mv temp_folder_cache $1