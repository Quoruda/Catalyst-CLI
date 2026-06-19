# Catalyst-CLI: AI Developer Context (AGENT.md)

This file provides critical architectural context for any LLM agent working on the Catalyst-CLI codebase. Read this before making modifications.

## 1. Core Architecture
Catalyst-CLI is a multi-agent orchestration framework running locally on the user's machine. 
- **`cli.py`**: The entry point. Handles the interactive shell (prompt-toolkit), slash commands (e.g., `/session delete *`), and session state persistence in `~/.catalyst/`.
- **`discovery.py`**: The auto-discovery engine. It automatically loads Tools, Engines, and Agents from their respective folders by inspecting exports and markdown schemas.
- **`providers.py`**: The LLM abstraction layer using `litellm`. It supports dynamic provider switching (OpenAI, Gemini, Ollama/OpenWebUI).

## 2. Agent Ecosystem (`agents/`)
Agents are defined purely in Markdown files with YAML front-matter.
- **`catalyst.md`**: The orchestrator (ReAct engine). It has NO reading tools (`read_file`, etc.) to prevent context overflow. Its sole purpose is to understand the user's intent and delegate strictly to specialized sub-agents.
- **`executor.md`**: The workhorse (PlanExecute engine). Equipped with bash and file writing tools. Handles complex tasks step-by-step. Rule: Must use `write_file` or `append_file` to persist text/reports (no text in-memory only).
- **`report_writer.md`**: Specialized document writer. Uses `append_file` to draft long documents incrementally to avoid JSON timeout limits on large context windows.
- **`code_reviewer.md` & `git_expert.md`**: Specialized analytical and version-control delegates.

## 3. Engines (`engines/`)
- **ReAct (`react.py`)**: Loop of Thought -> Action -> Observation. Max limit is 25 steps to prevent infinite loops. Ideal for dynamic, conversational routing.
- **PlanExecute (`plan_execute.py`)**: Generates an initial multi-step JSON plan, then executes each step. It maintains a persistent `execution_history` across steps to keep full context of the operation.

## 4. Tools (`tools/`)
Tools are standard Python functions. To register a new tool:
1. Write the Python function.
2. Define the JSON schema dictionary.
3. Append the schema to the `schemas` list at the bottom of the file.
4. Export the function in `tools/__init__.py`.
*Note*: `append_file` was recently added to `file_ops.py` to allow agents to build large files block-by-block without triggering LLM context limit crashes.

## 5. Coding Conventions & Safety
- **No Placeholders**: When modifying Python code or Markdown files, write fully functional code. Never use `pass`, `// TODO`, or `...`.
- **Atomic Commits**: Git changes should be committed logically and incrementally using the `Bash Agent` or `run_command` tool.
- **LLM Limits**: Keep in mind that external models (like local Qwen 27B) may crash if passed massive context. Encourage modular delegation rather than dumping the whole codebase into context.
