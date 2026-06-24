import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion

class SlashCommandCompleter(Completer):
    def __init__(self, command_tree):
        self.command_tree = command_tree
        
    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        if not text.startswith("/"):
            return
            
        parts = text.split()
        if len(parts) == 1 and not text.endswith(" "):
            word = parts[0]
            for cmd in self.command_tree:
                if cmd.startswith(word):
                    yield Completion(cmd, start_position=-len(word))
        elif len(parts) == 1 and text.endswith(" "):
            cmd = parts[0].lower()
            if cmd in self.command_tree:
                for sub in self.command_tree[cmd]:
                    yield Completion(sub, start_position=0)
        elif len(parts) == 2 and not text.endswith(" "):
            cmd = parts[0].lower()
            sub_word = parts[1]
            if cmd in self.command_tree:
                for sub in self.command_tree[cmd]:
                    if sub.startswith(sub_word):
                        yield Completion(sub, start_position=-len(sub_word))
import json
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style

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

SESSIONS_DIR = os.path.join(USER_CATALYST_DIR, "sessions")

def get_session_path(session_id: str) -> str:
    return os.path.join(SESSIONS_DIR, f"{session_id}.json")

def create_new_session() -> str:
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    from datetime import datetime
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def load_session(session_id: str) -> list:
    path = get_session_path(session_id)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("history", [])
        except Exception:
            pass
    return []

def save_session(session_id: str, history: list, agent_name: str, custom_title: str = None):
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = get_session_path(session_id)
    
    title = "Empty Session"
    is_custom_title = False
    
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                old_data = json.load(f)
                if old_data.get("is_custom_title"):
                    title = old_data.get("title", title)
                    is_custom_title = True
        except Exception:
            pass
            
    if custom_title is not None:
        title = custom_title
        is_custom_title = True
    elif not is_custom_title:
        for msg in history:
            if msg.get("role") == "user":
                title = msg.get("content", "")[:40] + "..."
                break
                
    from datetime import datetime
    data = {
        "id": session_id,
        "title": title,
        "is_custom_title": is_custom_title,
        "agent": agent_name,
        "updated_at": datetime.now().isoformat(),
        "history": history
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def list_sessions() -> list:
    import glob
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    sessions = []
    for path in glob.glob(os.path.join(SESSIONS_DIR, "*.json")):
        try:
            with open(path, "r", encoding="utf-8") as f:
                sessions.append(json.load(f))
        except Exception:
            pass
    sessions.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return sessions

import fcntl
import atexit

class SessionLocker:
    def __init__(self):
        self.lock_file = None
        self.fd = None
        
    def lock(self, session_id: str) -> bool:
        self.unlock()
        lock_path = get_session_path(session_id) + ".lock"
        try:
            self.fd = open(lock_path, 'w')
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_file = lock_path
            self.fd.write(str(os.getpid()))
            self.fd.flush()
            return True
        except (IOError, OSError):
            if self.fd:
                self.fd.close()
                self.fd = None
            return False
            
    def unlock(self):
        if self.fd and self.lock_file:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_UN)
                self.fd.close()
                if os.path.exists(self.lock_file):
                    os.remove(self.lock_file)
            except Exception:
                pass
            self.fd = None
            self.lock_file = None

session_locker = SessionLocker()
atexit.register(session_locker.unlock)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Catalyst CLI")
    parser.add_argument("-m", "--message", type=str, help="Quickly send a message and get a response without entering interactive mode.")
    parser.add_argument("-a", "--agent", type=str, help="Specify the agent to use.")
    parser.add_argument("-s", "--session", type=str, help="Specify a session ID to resume.")
    parser.add_argument("--sessions", action="store_true", help="List all saved sessions and exit.")
    parser.add_argument("--agents", action="store_true", help="List all registered agents and exit.")
    parser.add_argument("--tools", action="store_true", help="List all registered tools and exit.")
    parsed_args = parser.parse_args()

    console = Console()
    
    from discovery import available_agents
    if not available_agents:
        console.print(Panel("[bold red]Error: No agents registered. Please define at least one agent in the 'agents/' directory.[/bold red]", title="Error"))
        sys.exit(1)
        
    user_config = load_user_config()
    if "providers" not in user_config:
        user_config["providers"] = {
            "default": {
                "provider": os.getenv("LLM_PROVIDER", "ollama").lower(),
                "model": os.getenv("LLM_MODEL", "mistral:latest"),
                "api_base": os.getenv("LLM_API_BASE", ""),
                "api_key": os.getenv("LLM_API_KEY", ""),
                "temperature": float(os.getenv("LLM_TEMPERATURE", "0.0"))
            }
        }
        user_config["active_provider"] = "default"
        save_user_config(user_config)
        
    def apply_provider(provider_name: str):
        providers = user_config.get("providers", {})
        if provider_name in providers:
            cfg = providers[provider_name]
            from config import active_config
            active_config.provider = cfg.get("provider", "")
            active_config.model = cfg.get("model", "")
            active_config.api_base = cfg.get("api_base") or None
            active_config.api_key = cfg.get("api_key") or None
            active_config.temperature = float(cfg.get("temperature", 0.0))
            
            from discovery import available_agents
            for agent in available_agents.values():
                agent._catalyst_agent = None

    active_provider = user_config.get("active_provider")
    if active_provider:
        apply_provider(active_provider)

    if parsed_args.sessions:
        sessions = list_sessions()
        if not sessions:
            console.print("[yellow]No saved sessions.[/yellow]")
        else:
            console.print("[bold cyan]Saved Sessions:[/bold cyan]")
            current_id = user_config.get("current_session_id", "")
            for s in sessions:
                active_mark = "*" if s["id"] == current_id else " "
                console.print(f"{active_mark} [bold green]{s['id']}[/bold green] - [yellow]{s['title']}[/yellow] (Agent: {s.get('agent', 'unknown')})")
        sys.exit(0)

    if parsed_args.agents:
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
        sys.exit(0)

    if parsed_args.tools:
        from tools import tools_schema
        if not tools_schema:
            console.print("[yellow]No tools registered.[/yellow]")
        else:
            console.print("[bold cyan]Registered Tools:[/bold cyan]")
            for schema in tools_schema:
                desc = schema.get("description", "No description provided.")
                console.print(f"[bold green]{schema['name']}[/bold green] - {desc}")
        sys.exit(0)

    target_session_id = None
    loaded_history = []

    if parsed_args.session:
        target_session_id = parsed_args.session
        if not session_locker.lock(target_session_id):
            console.print(f"[bold red]Session '{target_session_id}' is currently in use by another terminal.[/bold red]")
            sys.exit(1)
        
        path = get_session_path(target_session_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    loaded_history = data.get("history", [])
            except Exception:
                pass
        else:
            console.print(f"[red]Session '{target_session_id}' not found.[/red]")
            sys.exit(1)

    saved_agent = user_config.get("default_agent")
    if parsed_args.agent:
        if parsed_args.agent not in available_agents:
            console.print(Panel(f"[bold red]Error: Agent '{parsed_args.agent}' not found. Registered agents: {', '.join(available_agents.keys())}[/bold red]", title="Error"))
            sys.exit(1)
        current_agent_name = parsed_args.agent
    elif saved_agent and saved_agent in available_agents:
        current_agent_name = saved_agent
    else:
        current_agent_name = "metamorph" if "metamorph" in available_agents else list(available_agents.keys())[0]
    
    try:
        react_agent = available_agents[current_agent_name]
    except Exception as e:
        console.print(Panel(f"[red]Error initializing agent: {str(e)}[/red]", title="Error"))
        sys.exit(1)
        
    if not parsed_args.message:
        os.system('cls' if os.name == 'nt' else 'clear')
        ascii_art = r"""
  ____      _        _           _   
 / ___|__ _| |_ __ _| |_   _ ___| |_ 
| |   / _` | __/ _` | | | | / __| __|
| |__| (_| | || (_| | | |_| \__ \ |_ 
 \____\__,_|\__\__,_|_|\__, |___/\__|
                       |___/         
"""
        console.print(f"[bold cyan]{ascii_art}[/bold cyan]")
        console.print("[dim]Interactive Supervisor Agent (ReAct Mode)[/dim]\n")
    
    if target_session_id:
        current_session_id = target_session_id
        history = loaded_history
        user_config["current_session_id"] = current_session_id
        save_user_config(user_config)
    else:
        current_session_id = create_new_session()
        session_locker.lock(current_session_id)
        user_config["current_session_id"] = current_session_id
        save_user_config(user_config)
        history = []
    
    def format_tokens(num: int) -> str:
        if num >= 1_000_000:
            return f"{num / 1_000_000:.2f}M"
        elif num >= 1_000:
            return f"{num / 1_000:.1f}k"
        return str(num)

    def get_toolbar_text():
        cwd = os.getcwd()
        history_count = len(history) // 2
        from metrics import global_metrics
        ctx_size = getattr(react_agent, "last_context_size", 0)
        formatted_ctx = format_tokens(ctx_size)
        formatted_total = format_tokens(global_metrics.total_tokens)
        cost_str = f" (${global_metrics.total_cost:.4f})" if global_metrics.total_cost > 0 else ""
        return [
            ("class:toolbar-label", f" Catalyst (Agent: {current_agent_name}) | "),
            ("class:toolbar-value", f"ID: {current_session_id} | "),
            ("class:toolbar-value", f"Ctx: {formatted_ctx}t | "),
            ("class:toolbar-value", f"Session: {formatted_total}t{cost_str} | "),
            ("class:toolbar-value", f"Model: {react_agent.catalyst_agent.config.model} | "),
            ("class:toolbar-value", f"Turns: {history_count}"),
        ]
        
    style = Style.from_dict({
        "bottom-toolbar": "bg:#222222 #ffffff",
        "toolbar-label": "fg:#00ffff bold",
        "toolbar-value": "fg:#bbbbbb",
    })
    
    command_tree = {
        "/exit": [],
        "/quit": [],
        "/clear": [],
        "/history": [],
        "/help": [],
        "/agent": ["list", "switch"],
        "/tool": ["list"],
        "/session": ["list", "resume", "new", "rename", "delete", "pop"],
        "/provider": ["list", "switch"]
    }
    completer = SlashCommandCompleter(command_tree)
    session = PromptSession(
        history=InMemoryHistory(),
        completer=completer,
        complete_while_typing=True,
        bottom_toolbar=get_toolbar_text
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
                if detail:
                    from rich.markup import escape
                    clean_detail = detail.replace('\n', ' ')
                    console.print(f"{indent}│ \\[{agent_name}] [green]Thinking:[/] {escape(clean_detail)}", overflow="ellipsis", no_wrap=True)
                else:
                    console.print(f"{indent}│ \\[{agent_name}] [green]Thinking[/]", overflow="ellipsis", no_wrap=True)
        elif step_type == "route":
            if active_status:
                active_status.stop()
                active_status = None
            from rich.markup import escape
            clean_detail = detail.replace('\n', ' ') if detail else ""
            console.print(f"{indent}│ \\[{agent_name}] [cyan]Route:[/] {escape(clean_detail)}", overflow="ellipsis", no_wrap=True)
        elif step_type == "action":
            if active_status:
                active_status.stop()
                active_status = None
            from rich.markup import escape
            clean_detail = detail.replace('\n', ' ') if detail else ""
            console.print(f"{indent}│ \\[{agent_name}] [magenta]Action:[/] [bold]{escape(name)}[/] [dim]({escape(clean_detail)})[/]", overflow="ellipsis", no_wrap=True)
        elif step_type == "error":
            if active_status:
                active_status.stop()
                active_status = None
            from rich.markup import escape
            clean_detail = detail.replace('\n', ' ') if detail else ""
            console.print(f"{indent}│ \\[{agent_name}] [bold red]Error:[/] {escape(clean_detail)}", overflow="ellipsis", no_wrap=True)
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
            response = react_agent.run(parsed_args.message, history, step_callback=step_callback)
            save_session(current_session_id, history, current_agent_name)
            console.print(Panel(Markdown(response), title="[bold green]Final Answer[/bold green]", border_style="green"))
            console.print()
        except Exception as e:
            from rich.markup import escape
            console.print(Panel(f"[bold red]Error: {escape(str(e))}[/bold red]", border_style="red"))
        finally:
            if active_status:
                active_status.stop()
        sys.exit(0)

    is_generating = False
    while True:
        try:
            prompt_str = f"[{current_agent_name}] >>> "
            user_input = session.prompt(
                prompt_str,
                bottom_toolbar=get_toolbar_text,
                style=style
            )
            if not user_input.strip():
                continue
                
            if user_input.lower() in ("/exit", "exit", "quit", "/quit"):
                user_config["default_agent"] = current_agent_name
                user_config["current_session_id"] = current_session_id
                save_user_config(user_config)
                save_session(current_session_id, history, current_agent_name)
                console.print("[yellow]Exiting Catalyst.[/yellow]")
                break
                
            if user_input.startswith("/"):
                parts = user_input.split(maxsplit=2)
                cmd = parts[0].lower()
                
                if cmd == "/clear":
                    console.clear()
                    continue
                    
                if cmd == "/history":
                    if not history:
                        console.print("[yellow]History is empty.[/yellow]")
                    else:
                        for msg in history:
                            role = msg["role"].upper()
                            color = "green" if role == "USER" else "yellow" if role == "SYSTEM" else "cyan"
                            console.print(f"[{color}][bold]{role}:[/bold] {msg['content']}[/{color}]")
                    continue
                    
                if cmd == "/agent":
                    if len(parts) >= 2:
                        subcmd = parts[1].lower()
                        if subcmd == "list":
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
                            
                        elif subcmd == "switch" and len(parts) >= 3:
                            target_agent = parts[2].strip()
                            from discovery import available_agents
                            if target_agent not in available_agents:
                                console.print(f"[red]Agent '{target_agent}' not found. Type /agent list to see available agents.[/red]")
                                continue
                            
                            current_agent_name = target_agent
                            react_agent = available_agents[current_agent_name]
                            history.clear()
                            user_config["default_agent"] = current_agent_name
                            user_config["current_session_id"] = current_session_id
                            save_user_config(user_config)
                            save_session(current_session_id, history, current_agent_name)
                            console.print(Panel(
                                f"[bold green]Switched to agent: {current_agent_name}[/bold green]\n"
                                f"[dim]Conversation history has been cleared for the new agent.[/dim]",
                                border_style="green"
                            ))
                            continue
                            
                    console.print("[yellow]Usage: /agent list | /agent switch <name>[/yellow]")
                    continue
                    
                if cmd == "/provider":
                    if len(parts) >= 2:
                        subcmd = parts[1].lower()
                        if subcmd == "list":
                            providers = user_config.get("providers", {})
                            if not providers:
                                console.print("[yellow]No providers configured in ~/.catalyst/config.json[/yellow]")
                            else:
                                console.print("[bold cyan]Configured Providers:[/bold cyan]")
                                active = user_config.get("active_provider")
                                for p_name, cfg in providers.items():
                                    mark = "*" if p_name == active else " "
                                    console.print(f"{mark} [bold green]{p_name}[/bold green] -> {cfg.get('provider')}/{cfg.get('model')}")
                            continue
                            
                        elif subcmd == "switch" and len(parts) >= 3:
                            p_name = parts[2].strip()
                            if p_name in user_config.get("providers", {}):
                                user_config["active_provider"] = p_name
                                save_user_config(user_config)
                                apply_provider(p_name)
                                console.print(f"[bold green]Switched provider to '{p_name}'.[/bold green]")
                            else:
                                console.print(f"[bold red]Provider '{p_name}' not found.[/bold red]")
                            continue
                            
                    console.print("[yellow]Usage: /provider list | /provider switch <name>[/yellow]")
                    continue
                    
                if cmd == "/tool":
                    if len(parts) >= 2:
                        subcmd = parts[1].lower()
                        if subcmd == "list":
                            from tools import tools_schema
                            if not tools_schema:
                                console.print("[yellow]No tools registered.[/yellow]")
                            else:
                                console.print("[bold cyan]Registered Tools:[/bold cyan]")
                                for schema in tools_schema:
                                    desc = schema.get("description", "No description provided.")
                                    console.print(f"[bold green]{schema['name']}[/bold green] - {desc}")
                            continue
                    console.print("[yellow]Usage: /tool list[/yellow]")
                    continue
                    
                if cmd == "/session":
                    if len(parts) >= 2:
                        subcmd = parts[1].lower()
                        if subcmd == "list":
                            sessions = list_sessions()
                            if not sessions:
                                console.print("[yellow]No saved sessions.[/yellow]")
                            else:
                                console.print("[bold cyan]Saved Sessions:[/bold cyan]")
                                for s in sessions:
                                    active_mark = "*" if s["id"] == current_session_id else " "
                                    console.print(f"{active_mark} [bold green]{s['id']}[/bold green] - [yellow]{s['title']}[/yellow] (Agent: {s.get('agent', 'unknown')})")
                                console.print("\n[dim]Use /session resume <id> to load a session, or /session new to start a new one.[/dim]")
                            continue
                            
                        elif subcmd == "new":
                            new_id = create_new_session()
                            session_locker.lock(new_id)
                            current_session_id = new_id
                            history.clear()
                            user_config["current_session_id"] = current_session_id
                            save_user_config(user_config)
                            save_session(current_session_id, history, current_agent_name)
                            console.print(Panel("[bold green]Started a new empty session.[/bold green]", border_style="green"))
                            continue
                            
                        elif subcmd == "resume" and len(parts) >= 3:
                            target_id = parts[2].strip()
                            if not session_locker.lock(target_id):
                                console.print(f"[bold red]Session '{target_id}' is currently in use by another terminal.[/bold red]")
                                continue
                            
                            loaded_history = load_session(target_id)
                            if loaded_history or os.path.exists(get_session_path(target_id)):
                                current_session_id = target_id
                                history.clear()
                                history.extend(loaded_history)
                                user_config["current_session_id"] = current_session_id
                                save_user_config(user_config)
                                console.print(Panel(f"[bold green]Resumed session: {target_id}[/bold green]\n[dim]Turns: {len(history)//2}[/dim]", border_style="green"))
                            else:
                                session_locker.unlock()
                                console.print(f"[red]Session '{target_id}' not found.[/red]")
                                session_locker.lock(current_session_id)
                            continue
                            
                        elif subcmd == "rename" and len(parts) >= 3:
                            new_name = parts[2].strip()
                            save_session(current_session_id, history, current_agent_name, custom_title=new_name)
                            console.print(Panel(f"[bold green]Session renamed to:[/bold green] {new_name}"))
                            continue
                            
                        elif subcmd == "delete" and len(parts) >= 3:
                            target_id = parts[2].strip()
                            if target_id == "*":
                                sessions = list_sessions()
                                deleted_count = 0
                                for sess in sessions:
                                    sess_id = sess.get("id")
                                    if not sess_id or sess_id == current_session_id:
                                        continue
                                    path = get_session_path(sess_id)
                                    if os.path.exists(path):
                                        temp_locker = SessionLocker()
                                        if temp_locker.lock(sess_id):
                                            try:
                                                os.remove(path)
                                                deleted_count += 1
                                            except Exception:
                                                pass
                                            finally:
                                                temp_locker.unlock()
                                console.print(f"[green]Deleted {deleted_count} inactive sessions.[/green]")
                                continue
                            
                            if target_id == current_session_id:
                                console.print("[red]Cannot delete the currently active session. Switch to another session first or use /session new.[/red]")
                                continue
                            
                            path = get_session_path(target_id)
                            if os.path.exists(path):
                                temp_locker = SessionLocker()
                                if temp_locker.lock(target_id):
                                    try:
                                        os.remove(path)
                                        console.print(f"[green]Session '{target_id}' deleted successfully.[/green]")
                                    except Exception as e:
                                        console.print(f"[red]Error deleting session: {e}[/red]")
                                    finally:
                                        temp_locker.unlock()
                                else:
                                    console.print(f"[red]Session '{target_id}' is in use and cannot be deleted.[/red]")
                            else:
                                console.print(f"[red]Session '{target_id}' not found.[/red]")
                            continue
                            
                        elif subcmd == "pop":
                            if not history:
                                console.print("[yellow]History is already empty.[/yellow]")
                                continue
                                
                            arg = parts[2].strip() if len(parts) >= 3 else "1"
                            
                            if arg == "*":
                                history.clear()
                                save_session(current_session_id, history, current_agent_name)
                                console.print("[yellow]Conversation history cleared for this session.[/yellow]")
                                continue
                                
                            try:
                                num_interactions = int(arg)
                                if num_interactions <= 0:
                                    raise ValueError()
                            except ValueError:
                                console.print("[red]Usage: /session pop [<number> | *][/red]")
                                continue
                                
                            total_removed = 0
                            actual_popped_interactions = 0
                            for _ in range(num_interactions):
                                if not history:
                                    break
                                last_role = history[-1].get("role")
                                history.pop()
                                total_removed += 1
                                if last_role == "assistant" and len(history) > 0 and history[-1].get("role") == "user":
                                    history.pop()
                                    total_removed += 1
                                actual_popped_interactions += 1
                                    
                            save_session(current_session_id, history, current_agent_name)
                            console.print(f"[green]Removed the last {actual_popped_interactions} interaction(s) ({total_removed} messages) from history.[/green]")
                            continue
                            
                    console.print("[yellow]Usage: /session list | /session new | /session resume <id> | /session rename <name> | /session delete <id> | /session pop [<number> | *][/yellow]")
                    continue

                if cmd == "/help":
                    console.print(Panel(
                        "[bold cyan]Available Commands:[/bold cyan]\n"
                        "[bold]/help[/bold] - Show this help menu\n"
                        "[bold]/agent list[/bold] - Show registered agents\n"
                        "[bold]/agent switch <name>[/bold] - Switch to a different agent\n"
                        "[bold]/tool list[/bold] - Show registered tools\n"
                        "[bold]/session list[/bold] - List all saved sessions\n"
                        "[bold]/session new[/bold] - Start a new blank session\n"
                        "[bold]/session resume <id>[/bold] - Resume a previous session\n"
                        "[bold]/session rename <name>[/bold] - Rename the current session\n"
                        "[bold]/session delete <id>[/bold] - Delete a session\n"
                        "[bold]/session pop [<number> | *][/bold] - Remove last N interactions (or '*' to clear all)\n"
                        "[bold]/provider list[/bold] - List available LLM providers\n"
                        "[bold]/provider switch <name>[/bold] - Switch active LLM provider\n"
                        "[bold]/history[/bold] - View current raw conversation history\n"
                        "[bold]/clear[/bold] - Clear the terminal screen\n"
                        "[bold]/exit[/bold] - Exit Catalyst",
                        title="Help",
                        border_style="cyan"
                    ))
                    continue

                console.print(f"[red]Unknown command: {user_input}. Type /help for available commands.[/red]")
                continue
                
            console.print()
            try:
                is_generating = True
                response = react_agent.run(user_input, history, step_callback=step_callback)
                save_session(current_session_id, history, current_agent_name)
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
            from rich.markup import escape
            console.print(Panel(f"[bold red]Error: {escape(str(e))}[/bold red]", border_style="red"))

if __name__ == "__main__":
    main()
