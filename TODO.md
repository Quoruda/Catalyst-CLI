# 🚀 Catalyst-CLI Roadmap & TODOs

This document tracks planned features, improvements, and architectural changes for the Catalyst-CLI project.

## 🗄️ Sessions & State Management
- [x] **Persistent Sessions**: Save message history to disk to allow resuming previous conversations.
- [x] **Session Locking**: Implement file locks to prevent multiple Catalyst processes from corrupting the same session.
- [x] **Session CLI Commands**: Add commands (e.g., `/sessions`, `/resume`) to manage and switch between active sessions.
- [x] **Ephemeral `-m` Flag**: Ensure that using the `-m` argument executes as a one-shot task and is intentionally NOT saved to any session history.

## 🖥️ User Interface (CLI)
- [x] **Agent Prompts**: Dynamically update the input prompt to reflect the active agent (e.g., `[deep_research] >>>`).
- [ ] **Startup Header**: Display a stylized ASCII Catalyst title upon launch.
- [x] **Clean Startup**: Automatically clear the terminal on boot for a cleaner UI.
- [x] **Persistent Footer**: Keep a persistent footer (status bar) displaying current model, token usage, and active mode.
- [ ] **Better token display**: better display token usage with proper units.

## 🧠 Models & Providers
- [ ] **Multi-Model Support**: Support switching between model sizes on the fly (e.g., large, medium, small) depending on the task's complexity.
- [ ] **Provider Configuration**: Allow registering and managing different providers (Ollama, Mistral, OpenAI) via a config file instead of relying entirely on `.env`.
- [x] **Token Estimation**: Implement a real-time token counter and cost estimator for active sessions and specific agents.

## 🛠️ Agents & Tools
- [x] **Clipboard Tool**: Create a tool to read from and write to the system clipboard.
- [ ] **Context Mapper**: Tool to build a visual or structural map of the current project directory.
- [ ] **Smart Commit & PR**: Agent/Tool to automatically generate semantic commits and draft pull requests.
- [ ] **TDD Buddy**: Specialized agent dedicated to writing and running unit tests based on specifications.
- [ ] **Boilerplate & Scaffold**: Tool to rapidly generate standard project structures.
- [ ] **Doc & Type Generator**: Tool to automatically generate docstrings, type hints, and documentation markdown.

---
*Note: This roadmap is a living document. Check off items as they are integrated into the main branch.*