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
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from agent import CatalystAgent
from react import ReActAgent

def main():
    console = Console()
    try:
        agent = CatalystAgent()
        react_agent = ReActAgent(agent)
    except Exception as e:
        console.print(Panel(f"[red]Error initializing agent: {str(e)}[/red]", title="Error"))
        sys.exit(1)
        
    console.print(Panel(
        "[bold cyan]CATALYST supervisor (ReAct Mode)[/bold cyan]",
        border_style="cyan"
    ))
    
    history = []
    
    def get_toolbar_text():
        cwd = os.getcwd()
        history_count = len(history) // 2
        return [
            ("class:toolbar-label", " Catalyst | "),
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
    
    completer = SlashCommandCompleter(["/exit", "/clear", "/help", "/history", "/tools"])
    session = PromptSession(
        history=InMemoryHistory(),
        completer=completer,
        complete_while_typing=True
    )
    
    active_status = None
    
    def step_callback(step_type: str, name: str, detail: str):
        nonlocal active_status
        if step_type == "thought":
            if name == "start":
                if active_status:
                    active_status.stop()
                active_status = console.status("[bold green]│ Thinking...[/]")
                active_status.start()
            elif name == "done":
                if active_status:
                    active_status.stop()
                    active_status = None
                console.print("│ [green]Thinking[/]")
        elif step_type == "action":
            if active_status:
                active_status.stop()
                active_status = None
            console.print(f"│ [magenta]Action:[/] [bold]{name}[/] [dim]({detail})[/]")
        elif step_type == "error":
            if active_status:
                active_status.stop()
                active_status = None
            console.print(f"│ [bold red]Error:[/] {detail}")

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
                console.print("[yellow]Exiting Catalyst.[/yellow]")
                break
                
            if user_input.lower() == "/clear":
                history.clear()
                console.print("[yellow]History cleared.[/yellow]")
                continue
                
            if user_input.lower() == "/help":
                console.print(Panel(
                    "[bold cyan]Available Commands:[/bold cyan]\n"
                    "[bold]/help[/bold] - Show this help menu\n"
                    "[bold]/tools[/bold] - Show registered tools and descriptions\n"
                    "[bold]/clear[/bold] - Clear conversation history\n"
                    "[bold]/history[/bold] - View current raw conversation history\n"
                    "[bold]/exit[/bold] - Exit Catalyst",
                    title="Help",
                    border_style="cyan"
                ))
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
                response = react_agent.run(user_input, history, step_callback=step_callback)
                console.print(Panel(Markdown(response), title="[bold green]Final Answer[/bold green]", border_style="green"))
                console.print()
            finally:
                if active_status:
                    active_status.stop()
                    active_status = None
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            console.print("\n[yellow]Exiting Catalyst.[/yellow]")
            break
        except Exception as e:
            console.print(Panel(f"[bold red]Error: {str(e)}[/bold red]", border_style="red"))

if __name__ == "__main__":
    main()
