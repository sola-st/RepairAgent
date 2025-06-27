# Auto-GPT: A GPT powered AI Assistant

## Configuration

- [hyperparams.json](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/hyperparams.json) Parameters for GPT
- [states_description.json](https://raw.githubusercontent.com/sola-st/RepairAgent/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/states_description.json) Descriptions by states
- [commands_by_state.json](https://raw.githubusercontent.com/sola-st/RepairAgent/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/commands_by_state.json) Commands by states
- [commands_interface](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/commands_interface.json) Interfaces by commands
- [cycle_instruction_text.txt](https://raw.githubusercontent.com/sola-st/RepairAgent/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/cycle_instruction_text.txt) Common instruction for prompt

## Initialization

- [main](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/cli.py#L104) Entry point for Auto GPT
  - [run_auto_gpt](http://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/main.py#L37) Start running Auto GPT
    - [create_config](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/configurator.py#L17) Update the config object with the given arguments
    - [with_command_modules](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/models/command_registry.py#L107) Create instance with registered commands
    - [construct_main_ai_config](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/main.py#L440) Construct the common prompt for AI
    - [Agent](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/agent.py#L36) Initiate Agent instance
      - [BaseAgent](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L32) Initiate Base Agent
        - [construct_full_prompt](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/config/ai_config.py#L105) Construct a prompt with the class information
        - [get_info](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/commands/defects4j_static.py#L11) Get info about a specific bug of a project
        - [run_tests](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/commands/defects4j_static.py#L66) Run tests on a given project with a bug number
          - [run_checkout](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/commands/defects4j_static.py#L139) Restore the original files
    - [run_interaction_loop](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/main.py#L203) Run the main interaction loop

## Interaction

- [_get_cycle_budget](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/main.py#L183) Get remaining command numbers
- [while cycles_remaining > 0](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/main.py#L253) Loop until no command remaining
  - [think](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L913) Deal with input and output for GPT API
    - [construct_prompt](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L1117) Construct and return a prompt
      - [construct_base_prompt](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L1009) Construct individual information
        - [construct_read_files](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L718) Construct contents of files that're already read
        - [construct_bug_report_context](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L765) Construct bug info, result and code of test cases
        - [construct_context_prompt](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L1009) Construct context such as hypothesises and fixes
    - [create_chat_completion](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/llm/utils/__init__.py#L96) Create a chat completion
      - [iopenai.create_chat_completion](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/llm/providers/openai.py#L239) Create a chat completion with OpenAI
        - [openai.ChatCompletion.create](https://platform.openai.com/docs/api-reference/chat/create) OpenAI Chat Completion API
    - [extract_dict_from_response](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/json_utils/utilities.py#L15) Extract code from response
      - [ast.literal_eval](https://docs.python.org/3/library/ast.html#ast.literal_eval) Extract abstract syntax tree from string
    - [detect_command_repetition](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/base.py#L357) Detect command repetition based on AST
  - [update_user](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/app/main.py#L332) Print the thought and the next command within the API response
  - [agent.execute](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/agent.py#L122) Execute command
    - [execute_command](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/agents/agent.py#L377) Execute the command and return the result
      - [task_complete](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/commands/system.py#L26) Method that would exit with goals accomplished
    - [history.add](https://github.com/sola-st/RepairAgent/blob/6591e7e5a895dbdc589f09795eea067c735f56f2/repair_agent/autogpt/llm/base.py#L117) Add result to history
