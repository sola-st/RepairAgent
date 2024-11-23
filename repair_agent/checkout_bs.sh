#!/bin/bash

# Function to get user input with a prompt
get_user_input() {
  read -p "$1" user_input
  echo "$user_input"
}

# Ask the user for project name
project_name=$(get_user_input "Project name: ")

# Ask the user for version
version=$(get_user_input "Version: ")

# Ask the user for the directory to write to
write_to=$(get_user_input "Write to: ")

# Construct the command
command="defects4j checkout -p $project_name -v $version -w $write_to"

# Execute the command
if $command; then
  echo "Checkout completed successfully!"
else
  echo "Checkout failed with an error."
fi
