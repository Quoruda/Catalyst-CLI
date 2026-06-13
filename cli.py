import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
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
    
    completer = WordCompleter(["/exit", "/clear", "/help", "/history"], ignore_case=True)
    session = PromptSession(
        history=InMemoryHistory(),
        completer=completer,
        complete_while_typing=True
    )
    
    def step_callback(step_type: str, name: str, detail: str):
        if step_type == "thought":
            if name:
                console.print(f"🤔 [yellow]Thought:[/] {name}")
        elif step_type == "action":
            console.print(f"⚙️ [magenta]Action:[/] [bold]{name}[/] [dim]({detail})[/]")
        elif step_type == "observation":
            lines = detail.splitlines()
            if len(lines) > 12:
                show_lines = lines[:4] + [f"  [dim]... ({len(lines) - 8} lines hidden) ...[/dim]"] + lines[-4:]
                display_text = "\n".join(show_lines)
            else:
                display_text = detail
            
            indented = "\n".join(f"  │ {line}" for line in display_text.splitlines())
            console.print(f"  [cyan]Observation:[/]\n{indented}")
        elif step_type == "error":
            console.print(f"❌ [bold red]Error:[/] {detail}")

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
                    "[bold]/clear[/bold] - Clear conversation history\n"
                    "[bold]/history[/bold] - View current raw conversation history\n"
                    "[bold]/exit[/bold] - Exit Catalyst",
                    title="Help",
                    border_style="cyan"
                ))
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
                
            console.print()
            with console.status("[bold blue]Thinking...[/bold blue]", spinner="dots"):
                response = react_agent.run(user_input, history, step_callback=step_callback)
                
            console.print(Panel(Markdown(response), title="[bold green]Final Answer[/bold green]", border_style="green"))
            console.print()
            
        except KeyboardInterrupt:
            continue
        except EOFError:
            console.print("\n[yellow]Exiting Catalyst.[/yellow]")
            break
        except Exception as e:
            console.print(Panel(f"[bold red]Error: {str(e)}[/bold red]", border_style="red"))

if __name__ == "__main__":
    main()
