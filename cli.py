import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
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
        f"[bold cyan]CATALYST supervisor (ReAct Mode)[/bold cyan]\n"
        f"[dim]Provider: {agent.config.provider.upper()} | Model: {agent.config.model} | Temp: {agent.config.temperature}[/dim]",
        border_style="cyan"
    ))
    
    history = []

    def step_callback(step_type: str, name: str, detail: str):
        if step_type == "thought":
            if name:
                console.print(Panel(name, title="[bold yellow]Thought[/bold yellow]", border_style="yellow"))
        elif step_type == "action":
            console.print(Panel(f"[bold magenta]{name}[/bold magenta]\n[dim]Args: {detail}[/dim]", title="[bold magenta]Action[/bold magenta]", border_style="magenta"))
        elif step_type == "observation":
            console.print(Panel(detail, title="[bold cyan]Observation[/bold cyan]", border_style="cyan"))
        elif step_type == "error":
            console.print(Panel(detail, title="[bold red]Error[/bold red]", border_style="red"))

    while True:
        try:
            user_input = Prompt.ask("[bold green]>>>[/bold green]")
            if not user_input.strip():
                continue
                
            if user_input.lower() in ("/exit", "exit", "quit"):
                console.print("[yellow]Exiting Catalyst.[/yellow]")
                break
                
            if user_input.lower() == "/clear":
                history.clear()
                console.print("[yellow]History cleared.[/yellow]")
                continue
                
            console.print()
            with console.status("[bold blue]Thinking...[/bold blue]", spinner="dots"):
                response = react_agent.run(user_input, history, step_callback=step_callback)
                
            console.print(Panel(Markdown(response), title="[bold green]Final Answer[/bold green]", border_style="green"))
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' or '/exit' to quit.[/yellow]")
        except Exception as e:
            console.print(Panel(f"[bold red]Error: {str(e)}[/bold red]", border_style="red"))

if __name__ == "__main__":
    main()
