import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion

class SlashCommandCompleter(Completer):
    def __init__(self, commands):
        self.commands = commands
        
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if text.startswith("/") and " " not in text:
            for cmd in self.commands:
                if cmd.startswith(text):
                    yield Completion(cmd, start_position=-len(text))
import json
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from agent import CatalystAgent
from react import ReActAgent

USER_CATALYST_DIR = os.path.expanduser("~/.catalyst")

def load_user_config() -> dict:
    config_path = os.path.join(USER_CATALYST_DIR, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_user_config(config: dict):
    try:
        os.makedirs(USER_CATALYST_DIR, exist_ok=True)
        config_path = os.path.join(USER_CATALYST_DIR, "config.json")
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass

def load_user_history() -> list:
    history_path = os.path.join(USER_CATALYST_DIR, "history.json")
    if os.path.exists(history_path):
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_user_history(history: list):
    try:
        os.makedirs(USER_CATALYST_DIR, exist_ok=True)
        history_path = os.path.join(USER_CATALYST_DIR, "history.json")
        with open(history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Catalyst CLI")
    parser.add_argument("-m", "--message", type=str, help="Quickly send a message and get a response without entering interactive mode.")
    parser.add_argument("-a", "--agent", type=str, help="Specify the agent to use.")
    parsed_args = parser.parse_args()

    console = Console()
    
    from discovery import available_agents
    if not available_agents:
        console.print(Panel("[bold red]Error: No agents registered. Please define at least one agent in the 'agents/' directory.[/bold red]", title="Error"))
        sys.exit(1)
        
    user_config = load_user_config()
    saved_agent = user_config.get("default_agent")
    if parsed_args.agent:
        if parsed_args.agent not in available_agents:
            console.print(Panel(f"[bold red]Error: Agent '{parsed_args.agent}' not found. Registered agents: {', '.join(available_agents.keys())}[/bold red]", title="Error"))
            sys.exit(1)
        current_agent_name = parsed_args.agent
    elif saved_agent and saved_agent in available_agents:
        current_agent_name = saved_agent
    else:
        current_agent_name = "catalyst" if "catalyst" in available_agents else list(available_agents.keys())[0]
    
    try:
        agent = CatalystAgent()
        react_agent = ReActAgent(agent, agent_name=current_agent_name)
    except Exception as e:
        console.print(Panel(f"[red]Error initializing agent: {str(e)}[/red]", title="Error"))
        sys.exit(1)
        
    if not parsed_args.message:
        console.print(Panel(
            "[bold cyan]CATALYST supervisor (ReAct Mode)[/bold cyan]",
            border_style="cyan"
        ))
    
    history = []
    
    def get_toolbar_text():
        cwd = os.getcwd()
        history_count = len(history) // 2
        return [
            ("class:toolbar-label", f" Catalyst (Agent: {current_agent_name}) | "),
            ("class:toolbar-value", f"Provider: {agent.config.provider.upper()} | "),
            ("class:toolbar-value", f"Model: {agent.config.model} | "),
            ("class:toolbar-value", f"Dir: {cwd} | "),
            ("class:toolbar-value", f"Turns: {history_count}"),
        ]
        
    style = Style.from_dict({
        "bottom-toolbar": "bg:#222222 #ffffff",
        "toolbar-label": "fg:#00ffff bold",
        "toolbar-value": "fg:#bbbbbb",
    })
    
    completer = SlashCommandCompleter(["/exit", "/clear", "/help", "/history", "/tools", "/agents", "/agent"])
    session = PromptSession(
        history=InMemoryHistory(),
        completer=completer,
        complete_while_typing=True
    )
    
    active_status = None
    
    def step_callback(step_type: str, name: str, detail: str):
        nonlocal active_status
        from discovery import nesting_level, active_agent_name
        level = nesting_level.get()
        indent = "  " * level
        agent_name = active_agent_name.get()
        if step_type == "thought":
            if name == "start":
                if active_status:
                    active_status.stop()
                active_status = console.status(f"[bold green]{indent}│ \\[{agent_name}] Thinking...[/]")
                active_status.start()
            elif name == "done":
                if active_status:
                    active_status.stop()
                    active_status = None
                console.print(f"{indent}│ \\[{agent_name}] [green]Thinking[/]")
        elif step_type == "action":
            if active_status:
                active_status.stop()
                active_status = None
            console.print(f"{indent}│ \\[{agent_name}] [magenta]Action:[/] [bold]{name}[/] [dim]({detail})[/]")
        elif step_type == "error":
            if active_status:
                active_status.stop()
                active_status = None
            console.print(f"{indent}│ \\[{agent_name}] [bold red]Error:[/] {detail}")
        elif step_type == "agent_start":
            if active_status:
                active_status.stop()
                active_status = None
            console.print(f"{indent}│ \\[{name}] [cyan]Started[/]")
        elif step_type == "agent_done":
            if active_status:
                active_status.stop()
                active_status = None
            console.print(f"{indent}│ \\[{name}] [cyan]Finished[/]")

    if parsed_args.message:
        console.print()
        try:
            response = react_agent.run(parsed_args.message, [], step_callback=step_callback)
            console.print(Panel(Markdown(response), title="[bold green]Final Answer[/bold green]", border_style="green"))
            console.print()
        except Exception as e:
            console.print(Panel(f"[bold red]Error: {str(e)}[/bold red]", border_style="red"))
        finally:
            if active_status:
                active_status.stop()
        sys.exit(0)

    is_generating = False
    while True:
        try:
            user_input = session.prompt(
                ">>> ",
                bottom_toolbar=get_toolbar_text,
                style=style
            )
            if not user_input.strip():
                continue
                
            if user_input.lower() in ("/exit", "exit", "quit"):
                save_user_config({"default_agent": current_agent_name})
                save_user_history(history)
                console.print("[yellow]Exiting Catalyst.[/yellow]")
                break
                
            if user_input.lower() == "/clear":
                history.clear()
                save_user_history(history)
                console.print("[yellow]History cleared.[/yellow]")
                continue
                
            if user_input.lower() == "/help":
                console.print(Panel(
                    "[bold cyan]Available Commands:[/bold cyan]\n"
                    "[bold]/help[/bold] - Show this help menu\n"
                    "[bold]/agent <name>[/bold] - Switch to a different agent (clears conversation history)\n"
                    "[bold]/agents[/bold] - Show registered agents and configurations\n"
                    "[bold]/tools[/bold] - Show registered tools and descriptions\n"
                    "[bold]/clear[/bold] - Clear conversation history\n"
                    "[bold]/history[/bold] - View current raw conversation history\n"
                    "[bold]/exit[/bold] - Exit Catalyst",
                    title="Help",
                    border_style="cyan"
                ))
                continue
                
            if user_input.lower().startswith("/agent ") or user_input.lower() == "/agent":
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    console.print(f"[yellow]Current active agent: {current_agent_name}[/yellow]")
                    continue
                
                target_agent = parts[1].strip()
                from discovery import available_agents
                if target_agent not in available_agents:
                    console.print(f"[red]Agent '{target_agent}' not found. Type /agents to see available agents.[/red]")
                    continue
                
                current_agent_name = target_agent
                react_agent = ReActAgent(agent, agent_name=current_agent_name)
                history.clear()
                save_user_config({"default_agent": current_agent_name})
                save_user_history(history)
                console.print(Panel(
                    f"[bold green]Switched to agent: {current_agent_name}[/bold green]\n"
                    f"[dim]Conversation history has been cleared for the new agent.[/dim]",
                    border_style="green"
                ))
                continue
                
            if user_input.lower() == "/agents":
                from discovery import available_agents
                if not available_agents:
                    console.print("[yellow]No agents registered.[/yellow]")
                else:
                    console.print("[bold cyan]Registered Agents:[/bold cyan]")
                    for name, agent_obj in available_agents.items():
                        engine = agent_obj.engine
                        desc = agent_obj.description
                        tools_list = ", ".join(agent_obj.tools)
                        console.print(f"[bold green]{name}[/bold green] (Engine: {engine}) - {desc}")
                        if tools_list:
                            console.print(f"  [dim]Tools:[/] {tools_list}")
                        else:
                            console.print("  [dim]Tools:[/] None")
                continue
                
            if user_input.lower() == "/tools":
                from tools import tools_schema
                if not tools_schema:
                    console.print("[yellow]No tools registered.[/yellow]")
                else:
                    console.print("[bold cyan]Registered Tools:[/bold cyan]")
                    for schema in tools_schema:
                        desc = schema.get("description", "No description provided.")
                        console.print(f"[bold green]{schema['name']}[/bold green] - {desc}")
                continue
                
            if user_input.lower() == "/history":
                if not history:
                    console.print("[yellow]History is empty.[/yellow]")
                else:
                    for msg in history:
                        role = msg["role"].upper()
                        color = "green" if role == "USER" else "yellow" if role == "SYSTEM" else "cyan"
                        console.print(f"[{color}][bold]{role}:[/bold] {msg['content']}[/{color}]")
                continue
                
            if user_input.startswith("/"):
                console.print(f"[red]Unknown command: {user_input}. Type /help for available commands.[/red]")
                continue
                
            console.print()
            try:
                is_generating = True
                response = react_agent.run(user_input, history, step_callback=step_callback)
                save_user_history(history)
                console.print(Panel(Markdown(response), title="[bold green]Final Answer[/bold green]", border_style="green"))
                console.print()
            finally:
                is_generating = False
                if active_status:
                    active_status.stop()
                    active_status = None
            
        except KeyboardInterrupt:
            if is_generating:
                console.print("\n[yellow]Generation cancelled by user.[/yellow]\n")
            else:
                console.print()
            continue
        except EOFError:
            save_user_config({"default_agent": current_agent_name})
            save_user_history(history)
            console.print("\n[yellow]Exiting Catalyst.[/yellow]")
            break
        except Exception as e:
            console.print(Panel(f"[bold red]Error: {str(e)}[/bold red]", border_style="red"))

if __name__ == "__main__":
    main()
