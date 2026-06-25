---
name: project_discovery
description: "Discovery and structural analysis of a codebase, reading local instructions (AGENT.md, README.md), and checking Git status."
tools:
  - generate_context_map
  - read_file
  - execute_bash
---
1. **Project Mapping**: When onboarding on a project or asked to analyze its architecture, use `generate_context_map` first to understand the global file structure.
2. **Guidelines and Documentation Search**: Actively look at the root for files like `AGENT.md`, `README.md`, `CONTRIBUTING.md`, or configurations (`package.json`, `pyproject.toml`, etc.). Read them using `read_file` to understand instructions, style conventions, and required technologies.
3. **Git Status**: Use `execute_bash` to run `git status` and `git log -n 5` to understand the working directory state, active branch, and recent changes.
4. **Validation Before Action**: Ensure you have a clear overview of the structure and local rules before making any code modifications.
