# 🚀 Catalyst-CLI Roadmap & TODOs

This document tracks planned features, improvements, and architectural changes for the Catalyst-CLI project.

## 🗄️ Sessions & State Management
- [x] **Persistent Sessions**: Save message history to disk to allow resuming previous conversations.
- [x] **Session Locking**: Implement file locks to prevent multiple Catalyst processes from corrupting the same session.
- [x] **Session CLI Commands**: Add commands (e.g., `/sessions`, `/resume`) to manage and switch between active sessions.
- [x] **Ephemeral `-m` Flag**: Ensure that using the `-m` argument executes as a one-shot task and is intentionally NOT saved to any session history.
- [x] **NameSessions**: Let the user rename sessions as they go. 
- [x] **DeleteSession**: Let the user delete sessions as they go. 

## 🖥️ User Interface (CLI)
- [x] **Agent Prompts**: Dynamically update the input prompt to reflect the active agent (e.g., `[deep_research] >>>`).
- [x] **Startup Header**: Display a stylized ASCII Catalyst title upon launch.
- [x] **Clean Startup**: Automatically clear the terminal on boot for a cleaner UI.
- [x] **Persistent Footer**: Keep a persistent footer (status bar) displaying current model, token usage, and active mode.
- [x] **Better token display**: better display token usage with proper units.

## 🧠 Models & Providers
- [ ] **Multi-Model Support**: Support switching between model sizes on the fly (e.g., large, medium, small) depending on the task's complexity.
- [x] **Provider Configuration**: Allow registering and managing different providers (Ollama, Mistral, OpenAI) via a config file instead of relying entirely on `.env`.
- [x] **Token Estimation**: Implement a real-time token counter and cost estimator for active sessions and specific agents.

## ⚙️ Cognitive Engines
- [ ] **Plan & Execute Engine**: Implement an engine that separates task planning from execution (ideal for highly complex, multi-step tasks).
- [ ] **Reflection Engine**: Create an iterative engine that generates a solution, critiques its own work, and refines it before returning the final answer.
- [ ] **Linear Chain Engine**: A deterministic, step-by-step engine without the ReAct loop for simpler, fast, and token-efficient pipelines.

## 🛠️ Agents & Tools
- [x] **Clipboard Tool**: Create a tool to read from and write to the system clipboard.
- [ ] **Context Mapper**: Tool to build a visual or structural map of the current project directory.
- [ ] **Git Agent**: Specialized agent to review recent diffs, stage files, generate semantic commits, and draft pull requests.
- [ ] **Code Reviewer Agent**: Reflection-based sub-agent that automatically reviews code changes for bugs/style before suggesting them.
- [ ] **Human-in-the-Loop (Critical Confirmation)**: (Optional) Interrupt and prompt the user for permission before running critical tools (like write_file or execute_bash) with visual diffs.
- [ ] **TDD Buddy**: Specialized agent dedicated to writing and running unit tests based on specifications.
- [ ] **Boilerplate & Scaffold**: Tool to rapidly generate standard project structures.
- [ ] **Doc & Type Generator**: Tool to automatically generate docstrings, type hints, and documentation markdown.
- [ ] **PDF Creator**: Tool and Agent to create and edit PDFs from Markdown.
- [ ] **Slide Deck Generator**: Tool and Agent to create presentations and slide decks from Markdown.
- [ ] **Image Search**: Tool and Agent to search for images online.

## 🧠 Memory & Personalization
- [ ] **Long-term Memory**: Implement a persistent profile (`memory.json`) for the agent to remember user preferences, name, and project contexts across sessions.

## 📚 Documentation & In-Context Learning
- [ ] **In-Context Doc Loader**: Support loading entire folders of markdown/text documentation directly into an agent's system prompt using a `docs` key in their configuration file (ideal for high-context models or local Ollama with prompt caching).
- [ ] **Dynamic Documentation Search (RAG)**: Create a tool that allows agents to query large local documentations via keyword/semantic search (fallback for low-context models).

---
*Note: This roadmap is a living document. Check off items as they are integrated into the main branch.*