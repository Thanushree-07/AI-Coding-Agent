# AI Coding Agent

A command-line coding agent built from scratch in Python. You type a task in plain English, and the agent uses tools to read, edit and run code by itself, step by step, until the task is done.

## What It Does

- Chats with an LLM (Groq, `openai/gpt-oss-20b`) and remembers the conversation
- Uses four tools: read files, list folders, edit files, run commands
- Keeps calling tools in a loop until the model gives a final text answer
- Asks for permission before editing files or running commands
- Stops after a maximum number of steps
- Prints a step-by-step log of everything the agent does

## Project Structure

```
AI-Coding-Agent/
├── agent.py            # tools, tool menu, and agent loop
├── requirements.txt    # groq, python-dotenv, pytest
├── .env                # API key (not committed)
├── .gitignore
├── playgrounds/        # folder the agent works in
└── logs/               # saved demo runs
```

## Setup

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Groq API key:
   ```
   GROQ_API_KEY=your-key-here
   ```
4. Run:
   ```
   python agent.py
   ```
   Type `quit` to exit.

## Tools

| Tool | What it does | Permission needed |
|---|---|---|
| `read_file(path)` | Returns the text of a file | No |
| `list_files(path)` | Lists the files in a folder | No |
| `edit_file(path, content)` | Replaces the whole contents of a file (creates the file and folders if missing) | Yes |
| `run_command(command)` | Runs a shell command and returns its output and errors | Yes |

Every tool catches its own errors and returns them as text, so the model can read the error and try something else.

## How the Agent Works

The model runs on Groq's servers and can only produce text. It cannot open files or run code. To act on the computer, it sends a **tool request** and the Python code does the work.

1. **Tool menu.** The `tools` list describes each tool to the model: its name, what it does, and its inputs. The model never sees the Python functions, only this description.
2. **Tool request.** When the model needs a tool, its reply has `tool_calls` filled in instead of text. The code checks `if msg.tool_calls` to tell the two cases apart.
3. **Running the tool.** The tool's inputs arrive as JSON text. `json.loads` turns them into a dictionary. The dictionary `available_tools` maps the tool name to the real function, and `func(**args)` calls it with those inputs.
4. **Sending the result back.** The result is added to the conversation with `role: "tool"` and the `tool_call_id` of the request it answers. The model's own request is saved first, because the API needs to see the request before the result.
5. **The loop.** The code calls the model again with the result. If the model asks for another tool, the loop repeats. The loop is a `while msg.tool_calls:`, so it keeps going until the model replies with plain text, which is the final answer.

```
User task
   |
   v
Model --> tool request --> permission check --> run tool --> result
   ^                                                            |
   |____________________ result sent back ______________________|
   |
   v (no more tool requests)
Final answer
```

## Safety Features

- **Permission prompts:** `edit_file` and `run_command` show what they will do and wait for `y` or `n`. If the user says `n`, "User has denied this action" is sent back to the model.
- **Step limit:** the loop stops after `MAX_STEPS` rounds so the agent cannot run forever.
- **Command timeout:** shell commands are stopped after 30 seconds.
- **API key protection:** the key is stored in `.env`, which is listed in `.gitignore`.

## Log Output

Each step prints labelled lines so the agent's reasoning can be followed:

| Label | Meaning |
|---|---|
| `STEP n` | One round of the loop |
| `[AI DECIDED]` | The tool and inputs the model chose |
| `[PERMISSION]` | The user is asked to approve |
| `[APPROVED]` / `[DENIED]` / `[AUTO]` | What happened to the request |
| `[RESULT]` | What the tool returned |
| `[SENDING RESULTS BACK TO AI...]` | The result goes back to the model |

## Demo 1: Fixing a Bug

Prompt: `run playgrounds/buggy.py and fix it if it fails`

`buggy.py` contained `print("Total:" + 5)`, which fails because text and a number cannot be added.

```
TOOL CALLED: run_command {'command': 'python playgrounds/buggy.py'}
TOOL CALLED: list_files {'path': 'playgrounds'}
TOOL CALLED: read_file {'path': 'playgrounds/buggy.py'}
TOOL CALLED: edit_file {'content': 'print("Total " + str(5))', 'path': 'playgrounds/buggy.py'}
TOOL CALLED: run_command {'command': 'python playgrounds/buggy.py'}
AI : The script now prints "Total 5" with a space between "Total" and the number.
```

From one sentence, the agent ran the file, saw the error, looked at the folder, read the code, fixed it, and ran it again to confirm.

## Demo 2: Creating a Calculator With Tests

Prompt: `Create playgrounds/calculator.py with add, subtract, multiply and divide functions, then write a test file for it and run the tests.`

The full run is saved in `logs/log1_failure_recovery.txt`. The agent:

1. Wrote `calculator.py` after the user approved the edit
2. Failed to write a test file because the `tests/` folder did not exist
3. Listed the files, retried, and tried to create the folder
4. Wrote the test file, then tried to run `pytest`, which was not installed
5. Was stopped by the step limit

## Improvements Made After Demo 2

- **Folder restriction:** the system prompt tells the agent to work only inside `playgrounds/`, after it listed the whole drive
- **Folder creation:** `edit_file` now creates missing folders, after the write failed three times
- **Windows commands:** the system prompt states the OS and uses `python -m pytest`, after the agent used Linux commands
- **pytest:** added to `requirements.txt`
- **Step limit:** raised to 15, since real tasks need more rounds

A second run after these fixes is saved in `logs/log2_clean_success.txt`.

## Limitations

- `edit_file` replaces the whole file, so the model must send the full text and anything left out is lost
