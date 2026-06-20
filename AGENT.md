# Catalyst-CLI: AI Developer Context (AGENT.md)

This file provides critical architectural context and behavioral guidelines for any LLM agent working on the Catalyst-CLI codebase. Read this before making modifications.

## 1. Core Philosophy: Local-First & Privacy-First
Catalyst-CLI is designed to operate locally on the user's machine with maximum control and minimal external dependencies:
- **Local Execution**: All major operations—such as executing commands, compiling files, parsing documents, and rendering diagrams—must run locally on the user's host.
- **Privacy-First**: Do not send user data, code, or documents to external third-party web APIs unless it is an explicitly configured fallback or requested by the user. 
- **Offline Operations**: Tools (like diagram generation) must prioritize utilizing local binaries (e.g., `mermaid-cli`) over online rendering endpoints.

## 2. Core Architecture
Catalyst-CLI is a multi-agent orchestration framework running locally on the user's machine. 
- **`cli.py`**: The entry point. Handles the interactive shell (prompt-toolkit), slash commands (e.g., `/session pop`), and session state persistence in `~/.catalyst/`.
- **`discovery.py`**: The auto-discovery engine. It automatically loads Tools, Engines, and Agents from their respective folders by inspecting exports and markdown schemas.
- **`providers.py`**: The LLM abstraction layer using `litellm`. It supports dynamic provider switching (OpenAI, Gemini, Ollama/OpenWebUI).

## 3. Agent Ecosystem (`agents/`)
Agents are defined purely in Markdown files with YAML front-matter.
- **`catalyst.md`**: The orchestrator (ReAct engine). It acts strictly as an **Executive Manager**. Its sole purpose is to understand high-level objectives, delegate to specialized sub-agents, and coordinate results. It must never attempt to perform heavy file reading, writing, or analysis tasks itself.
- **`executor.md`**: The workhorse (PlanExecute engine). Equipped with bash and file writing tools. Handles complex tasks step-by-step. Rule: Must use `write_file` or `append_file` to persist text/reports (no text in-memory only).
- **`report_writer.md`**: Specialized document writer. Uses `append_file` to draft long documents incrementally to avoid JSON timeout limits on large context windows.
- **`code_reviewer.md` & `git_expert.md`**: Specialized analytical and version-control delegates.

## 4. Engines (`engines/`)
- **ReAct (`react.py`)**: Loop of Thought -> Action -> Observation. Max limit is 25 steps to prevent infinite loops. Ideal for dynamic, conversational routing.
- **PlanExecute (`plan_execute.py`)**: Generates an initial multi-step JSON plan, then executes each step. It maintains a trimmed step log to keep the LLM context usage low.

## 5. Tools (`tools/`)
Tools are standard Python functions. To register a new tool:
1. Write the Python function.
2. Define the JSON schema dictionary.
3. Append the schema to the `schemas` list at the bottom of the file.
4. Export the function in `tools/__init__.py`.
- **`generate_diagram.py`**: Generates PNG diagrams locally using `mmdc` (mermaid-cli).
- **`ask_document.py`**: Utilizes local parsing/summarizing for PDF documents.

## 6. Coding Conventions & Safety for AI Agents
When working on this codebase or acting as an agent within this system, you must strictly follow these rules:
- **No Placeholders**: Write fully functional, production-ready code. Never use `pass`, `// TODO`, or `...` points of ellipsis.
- **Double-Verification (Anti-Hallucination)**: 
  Before referencing, writing, or commenting on code variables, database fields, API routes, or file names, you MUST perform an exact search (e.g. `grep_search` or `read_file`) to check their exact spelling and structure in the source files. After creating or modifying files, cross-reference them with the source reference to verify accuracy.
- **Clean Code & No Redundant Comments**:
  Do not write obvious, redundant, or boilerplate comments (e.g., `# import libraries`, `# define variable x`). Write clean, self-documenting code. Do not write comments at all unless explaining complex, non-obvious logic.
- **Atomic Commits**: Git changes should be committed logically and incrementally. Group commits by feature/fix.
- **LLM Limits**: Keep in mind that local models (like local Qwen 27B) may crash if passed massive context. Encourage modular delegation rather than dumping the whole codebase into context.
