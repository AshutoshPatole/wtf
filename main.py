#!/usr/bin/env python3
"""
WTF - What's The F***ing command?
A simple CLI tool to generate shell commands from natural language.
"""

import os
import sys
import json
import platform
import argparse
from pathlib import Path
from google import genai
import pyperclip
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()


def get_env_file_path() -> Path:
    """Get the path to the .env file in the user's home directory"""
    config_dir = Path.home() / ".wtf"
    config_dir.mkdir(exist_ok=True)
    return config_dir / ".env"


def load_api_key_from_env_file() -> str | None:
    """Load API key from .env file if it exists"""
    env_file = get_env_file_path()
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GEMINI_API_KEY='):
                        return line.split('=', 1)[1].strip('"\'')
        except Exception:
            pass
    return None


def save_api_key_to_env_file(api_key: str) -> None:
    """Save API key to .env file"""
    env_file = get_env_file_path()
    try:
        with open(env_file, 'w') as f:
            f.write(f'GEMINI_API_KEY={api_key}\n')
        console.print(f"✓ API key saved to {env_file}", style="green")
    except Exception as e:
        console.print(f"⚠️  Could not save API key: {str(e)}", style="yellow")


def get_api_key() -> str:
    """Get API key from environment or .env file, or prompt user"""
    api_key = os.environ.get("GEMINI_API_KEY") or load_api_key_from_env_file()

    if not api_key:
        console.print("\n⚠️  No API key found.", style="yellow")
        console.print("Please get your API key from: https://aistudio.google.com/apikey\n")
        api_key = console.input("[cyan]Enter your Gemini API key:[/cyan] ").strip()

        if not api_key:
            console.print("❌ No API key provided. Exiting.", style="red")
            sys.exit(1)

        save_api_key_to_env_file(api_key)

    return api_key


def generate_command(query: str, show_explanation: bool = False) -> None:
    """Generate command from natural language query"""

    api_key = get_api_key()

    try:
        client = genai.Client(api_key=api_key)
        model_name = "gemini-2.5-flash"

        os_name = platform.system()
        shell_name = "PowerShell" if os_name == "Windows" else "Bash"

        prompt = f"""You are a command line expert. The user needs a command for {os_name} using {shell_name}.
Return a JSON object with three keys:
1. "command": The exact command to run (string).
2. "explanation": A brief one-line explanation of what the command does (string).
3. "detailed_explanation": A concise explanation in markdown format, similar to man pages:
   - Start with a brief description (1-2 lines)
   - List each flag/option with a one-line explanation using bullet points
   - Keep it concise and scannable
   - Use proper markdown formatting (headers, bullets, code blocks)

User Query: {query}

Output ONLY valid JSON, no markdown formatting."""

        console.print("🤔 Thinking...", style="yellow")

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        text = response.text.strip()

        # Clean up Markdown formatting if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        data = json.loads(text)

        if "command" not in data or "explanation" not in data or "detailed_explanation" not in data:
            raise ValueError("Response missing required fields")

        console.print("\r" + " " * 20 + "\r", end="")

        command = data['command']
        pyperclip.copy(command)
        shell_lang = "powershell" if os_name == "Windows" else "bash"

        syntax = Syntax(command, shell_lang, theme="monokai", line_numbers=False)
        console.print(Panel(syntax, title="[bold green]Command[/bold green]", border_style="green"))
        console.print(f"\n[dim]Command copied to clipboard[/dim]\n")

        # console.print(f"\n[dim]{data['explanation']}[/dim]\n")

        if show_explanation:
            md = Markdown(data['detailed_explanation'])
            console.print(Panel(md, title="[bold cyan]Detailed Explanation[/bold cyan]", border_style="cyan"))

    except json.JSONDecodeError as e:
        console.print(f"❌ Error parsing response: {str(e)}", style="red")
        console.print(f"Raw response: {text[:200]}", style="dim")
        sys.exit(1)
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        sys.exit(1)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="WTF - Generate shell commands from natural language",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  wtf "list files larger than 1024kb"
  wtf "find all python files modified in the last 7 days" -e
  wtf "kill process on port 3000" --explain
        """
    )

    parser.add_argument(
        "query",
        nargs="+",
        help="Natural language description of the command you need"
    )

    parser.add_argument(
        "-e", "--explain",
        action="store_true",
        help="Show detailed explanation of the command"
    )

    args = parser.parse_args()

    # Join query parts into a single string
    query = " ".join(args.query)

    if not query.strip():
        console.print("❌ Please provide a query", style="red")
        parser.print_help()
        sys.exit(1)

    generate_command(query, show_explanation=args.explain)


if __name__ == "__main__":
    main()