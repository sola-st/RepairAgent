# Versions history

## RepairAgent 0.1.0
- Try AutoGPT as-is for the task of program repair on defects4j

## RepairAgent 0.2.0
### Added
- integrated defects into the environement (docker container)

## RepairAgent 0.3.0
### Added
- A wrapper around defects4j commands
### Fixed
- remove unncessary commands from AutoGPT


## RepairAgent 0.4.0
### Added
### Fixed
- Change of the prompt format from history of commands and their output to structured prompt with different sections of information
- The last command and its output are added to the end of the prompt

## RepairAgent 0.5.0
### Added
- Adding states in which the model could exist and give the model the ability to transition to according to the above sketch, the three states are:
    * Collect more info to understand the bug
    * Collect more info to suggest a fix
    * Try out candidate fixes

### Fixed
- Simplify the structure of the output of the model by replacing the thoughts dictionary with just a text field

## RepairAgent 0.6.0
### Added
- Validate fix against hypothesis
    * Sometimes the model gives a hypothesis about the bug but then proceeds to suggest a fix that is irrelevant or does not reflect the hypothesis
    * Solution: validate whether the fix reflects the hypothesis. See example.
    * To be added: validate hypotheses against collected info: location, failing test…

### Fixed
- Minor updates of prompt structure
    * Change in order of sections
    * Redefinition of goals (rephrasing)
    * Technically: changed the handling of the prompt in code from text only to data structures (list, dict…)

- User message vs System message
    * GPT3.5 gives more attention to user input and less attention to system messages which caused the agent to ignore feedback from commands and guidelines given in the prompt ⇒ remove system messages
    * Only keep role description as a system message
    * The conversation would always be of the form: user input, assistant output, user input…

## RepairAgent 0.6.1

### Added
- Information of bug localization and initial running of test cases are added to the prompt

### Fixed
- remove the commands "get_info" and "run_tests" from the list of availbale commands.
- the method that parses the output of the model was updated to handle natural langauge around the json dictionary
- the command that writes the fix now receives a dictionary as input of changed lines to avoid inserting repetitive lines.
- path approximation now handles dotted paths
- fixed bug in prompt construction that lead into wrong information sections ("system"-->"user")

## RepairAgent 0.6.2

### Added
- add option to query for fix after each n queries (with 0 for disabled)
- bring back the command extract method code
- add budget tracking
    - No tracking ["NO-TRACK", None]
    - Full tracking ["FULL-TRACK", None]
    - Full tracking + aim to suggest n fixes ["FULL-TRACK", {"#fixes": ?}]
    - Forced transitioning ["FORCED", {"T1": ?, "T2":?}]
- summarize the result of trying multiple patches at ones
- add the list of suggested fixes to the prompt
### Fixed
- do not allow repetition of command execution
    - approach 1: after detecting repitition, instruct the model on next cycle to not use the repeated command
    - appraoch 2: after detecting repitition, instruct the model to suggested the top 3 commands and choose the one that avoids repitition
        - the first one that avoids
        - the one that avoids and have less frequency

- need to validate command args names otherwise they raise exception
        - Automatic mapping of commands arguments when wrong
        - Also, automatic mapping of some arguments values 
- remove history of commands (saturates the prompt)
- fixed the number of suggested fixes logged at the end of each cycle len(suggested_fixes) does not work
- handle the case of missing command name

## RepairAgent 0.6.3

### Added
- save/restore the progress (context) of the agent on a given instance
    - usefull to run the agent for more iterations later on
    - to recover from exceptions

- A new format for writing the fix which allows different kinds of changes across multiple files
    - it also easier for postprocessing

### Fixed
- fix the dependence on experiment configuration file
    - this implies that now we can run concurent agents with different configurations
    
### Future
- postprocess the suggested fix to validate the changed lines
    - produce patch as text and manually locate insertion location compare to lined numbers
    - modification in modified lines should respect a minimum threshold of similarity

- create a setup where after each query, we ask chatgpt whether the collected information is enough to fix the bug and if so suggest a fix, otherwise what type of information should we get next (only provide the next needed information. we acknowledge that we might need multiple peices of information but we want you to give us only one for now. we will give you the chance to ask for more later.).
    - At the end of each cycle we add the type of information to collect to the prompt of RepairAgent and it should produce a command that collects that information

- Execute all commands in each state (at least once then leave the model do whatever it wants)
- produce mutations of a line
    - produce variants of a fix
    - suggest relevant patterns