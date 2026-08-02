import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich import print as rprint

import config
from core.session import PracticeSession
from services import stt_service

console = Console()

def clear_screen():
    print("\033[H\033[J", end="")

def show_header():
    clear_screen()
    header_text = Text("C1 Speaking Assistant", style="bold blue", justify="center")
    console.print(Panel(header_text, border_style="blue"))

def handle_practice_session(current_config: dict):
    show_header()
    console.print(f"[dim]Starting session with model: {current_config['model_name']}[/dim]\n")
    console.print("Type your responses. Type [bold red]'exit'[/bold red] to finish and get your feedback.\n")
    
    session = PracticeSession(current_config)
    
    while True:
        try:
            console.print("[bold green]You[/bold green] (Speak or type): ", end="")
            user_input = stt_service.get_hybrid_input(prompt_text="")

            
            if user_input.lower() in ['exit', 'quit']:
                break
                
            if not user_input:
                continue
                
            ai_reply = session.process_user_input(user_input)
            
            if ai_reply.startswith("Error:"):
                console.print(f"[bold red]{ai_reply}[/bold red]")
                break
                
            console.print(f"\n[bold blue]Examiner[/bold blue]: {ai_reply}\n")
            
        except KeyboardInterrupt:
            break
            
    # Generate Feedback
    console.print("\n[dim]Analyzing session and generating feedback...[/dim]")
    result = session.end_session_and_generate_feedback()
    
    if isinstance(result, tuple):
        feedback, path = result
        console.print(Panel(feedback, title="Feedback Report", border_style="cyan"))
        if path:
            console.print(f"\n[green]Report saved successfully to:[/green] {path}")
    else:
        console.print(f"[red]{result}[/red]")
        
    Prompt.ask("\n[dim]Press Enter to return to the main menu[/dim]")

def handle_config_obsidian(current_config: dict):
    show_header()
    console.print(Panel("Configure Obsidian Vault Path", border_style="cyan"))
    console.print(f"Current Path: [yellow]{current_config['obsidian_path']}[/yellow]\n")
    
    new_path = Prompt.ask("Enter new absolute path (or press Enter to keep current)")
    
    if new_path:
        success = config.update_obsidian_path(current_config, new_path)
        if success:
            console.print("[green]Path updated successfully.[/green]")
        else:
            console.print("[red]Failed to update path. Ensure the directory is valid.[/red]")
            
    Prompt.ask("\n[dim]Press Enter to return to the main menu[/dim]")

import msvcrt

def interactive_select(options: list, current_selected: str = None) -> str:
    """Displays an interactive menu using arrow keys."""
    if not options:
        return ""
        
    selected_idx = 0
    if current_selected in options:
        selected_idx = options.index(current_selected)
        
    # Hide cursor
    sys.stdout.write("\033[?25l")
    
    try:
        while True:
            # Print the options
            for i, option in enumerate(options):
                prefix = "❯" if i == selected_idx else " "
                color = "[bold cyan]" if i == selected_idx else "[dim]"
                console.print(f" {prefix} {color}{option}[/]")
            
            # Read key
            key = msvcrt.getch()
            if key in (b'\x00', b'\xe0'): # Arrow keys prefix
                key = msvcrt.getch()
                if key == b'H': # Up arrow
                    selected_idx = (selected_idx - 1) % len(options)
                elif key == b'P': # Down arrow
                    selected_idx = (selected_idx + 1) % len(options)
            elif key == b'\r': # Enter
                break
                
            # Clear the lines
            sys.stdout.write(f"\033[{len(options)}A")
            sys.stdout.flush()
    finally:
        # Show cursor
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()
        
    return options[selected_idx]

def handle_config_model(current_config: dict):
    from services import llm_service
    show_header()
    console.print(Panel("Configure LLM Model", border_style="cyan"))
    console.print(f"Current Model: [yellow]{current_config['model_name']}[/yellow]\n")
    
    console.print("[dim]Fetching installed models from Ollama...[/dim]")
    models = llm_service.get_installed_models()
    
    if not models:
        console.print("[red]No models found. Please make sure Ollama is running and you have downloaded a model.[/red]")
        Prompt.ask("\n[dim]Press Enter to return to the main menu[/dim]")
        return
        
    # Clear the fetching message
    sys.stdout.write("\033[1A\033[2K")
    console.print("[bold]Select a model (Use ↑/↓ arrows, press Enter to confirm):[/bold]\n")
    
    new_model = interactive_select(models, current_selected=current_config['model_name'])
    
    if new_model and new_model != current_config['model_name']:
        success = config.update_model_name(current_config, new_model)
        if success:
            console.print(f"\n[green]Model updated to '{new_model}'.[/green]")
    else:
        console.print("\n[dim]Model unchanged.[/dim]")
            
    Prompt.ask("\n[dim]Press Enter to return to the main menu[/dim]")

def run():
    current_config = config.load_config()
    
    while True:
        show_header()
        
        console.print("1. Start Practice Session")
        console.print(f"2. Configure Obsidian Path [dim]({current_config['obsidian_path']})[/dim]")
        console.print(f"3. Configure LLM Model [dim]({current_config['model_name']})[/dim]")
        console.print("4. Exit\n")
        
        choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="1")
        
        if choice == "1":
            handle_practice_session(current_config)
        elif choice == "2":
            handle_config_obsidian(current_config)
        elif choice == "3":
            handle_config_model(current_config)
        elif choice == "4":
            console.print("\n[dim]Goodbye.[/dim]")
            sys.exit(0)
