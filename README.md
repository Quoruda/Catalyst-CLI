# Catalyst-CLI

Catalyst-CLI is an interactive command-line supervisor agent implementing the ReAct (Reasoning and Acting) execution pattern. It is designed to act as an assistant capable of reasoning and orchestrating local system operations, document ingestion, and visual analysis. 

The agent's backend is powered by LiteLLM, offering compatibility across multiple LLM providers including Google Gemini, OpenAI, and Ollama.

## Features

- Interactive Shell: Built with prompt-toolkit supporting line editing, arrow-key history traversal, custom auto-completions, and a live information toolbar.
- Slash Commands: Dedicated commands for session control including /help, /clear, /history, and /exit. Unknown slash commands are intercepted to prevent accidental LLM execution.
- Clean Execution Timeline: Real-time logging of the agent's reasoning loop using a vertical line connector. Shows active spinners during generation and permanent logs for completed steps without terminal clutter.
- Extensible Toolset:
  - System Shell Execution: execute_bash for running local terminal commands.
  - Document Reading: read_pdf powered by pymupdf4llm, with native context silencers preventing Tesseract OCR diagnostics from polluting stdout/stderr.
  - Image Analysis: view_image for visual understanding of local files (PNG, JPG, WEBP, GIF) via multimodal models.

## Requirements

The project requires Python 3.10+. Package dependencies are managed via `requirements.txt`.

## Installation

1. Clone the repository and navigate to the project directory:
```bash
git clone <repository-url>
cd Catalyst-CLI
```

2. Create and activate a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/env/activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the root directory:
```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.0
LLM_API_KEY=your-api-key-here
```

## Usage

Start the interactive CLI:
```bash
python cli.py
```

Inside the CLI, you can query the agent or run commands:
```
>>> List the PDF files in this directory and summarize them.

│ Thinking
│ Action: execute_bash ({"command": "ls *.pdf"})
│ Thinking
│ Action: read_pdf ({"filepath": "document.pdf"})
│ Thinking
```

### Supported Slash Commands

- /help: Display the command help menu.
- /clear: Clear the active session history.
- /history: Review the raw message exchanges.
- /exit: Terminate the session.