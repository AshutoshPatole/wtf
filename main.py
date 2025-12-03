import asyncio
import json
import os
import platform
from pathlib import Path

import pyperclip
from google import genai
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Header, Footer, Input, Static, RichLog, Markdown


class WTF(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 80%;
        height: auto;
        border: solid green;
        padding: 1 2;
    }

    #question {
        width: 100%;
        margin-bottom: 1;
    }

    #answer {
        width: 100%;
        height: auto;
        min-height: 3;
        border: solid blue;
        padding: 1;
    }

    #explanation {
        width: 100%;
        height: auto;
        max-height: 20;
        border: solid yellow;
        padding: 1;
        display: none;
        margin-top: 1;
        overflow-y: auto;
    }

    #output {
        width: 100%;
        height: 10;
        border: solid cyan;
        display: none;
        margin-top: 1;
    }

    #help-text {
        width: 100%;
        color: #00ff00;
        text-align: center;
        margin-top: 1;
        background: #1a1a1a;
        padding: 1;
    }

    .loading {
        color: yellow;
    }

    .error {
        color: red;
    }

    .success {
        color: green;
    }
    """

    BINDINGS = [
        Binding("e", "explain_command", "Explain", show=True),
        Binding("escape", "unfocus_input", "Unfocus", show=False),
        Binding("q", "quit", "Quit", show=True),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            yield Static("What command do you need?", classes="label")
            yield Input(placeholder="> show pods that crashed in the last 30 minutes in prod", id="question")
            yield Static("", id="answer")
            yield Markdown("", id="explanation")
            yield RichLog(id="output", wrap=True, highlight=True)
            yield Static("💡 [Enter] Generate Command | [ESC] Unfocus | [e] Explain | [q] Quit", id="help-text",
                         markup=False)
        yield Footer()

    @staticmethod
    def _get_env_file_path() -> Path:
        """Get the path to the .env file in the script's directory"""
        script_dir = Path(__file__).parent
        return script_dir / ".env"

    def _load_api_key_from_env_file(self) -> str | None:
        """Load API key from .env file if it exists"""
        env_file = self._get_env_file_path()
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

    def _save_api_key_to_env_file(self, api_key: str) -> None:
        """Save API key to .env file"""
        env_file = self._get_env_file_path()
        try:
            with open(env_file, 'w') as f:
                f.write(f'GEMINI_API_KEY={api_key}\n')
        except Exception as e:
            self.notify(f"⚠️  Could not save API key: {str(e)}", severity="warning")

    def on_mount(self) -> None:
        # Try to get API key from environment first, then from .env file
        api_key = os.environ.get("GEMINI_API_KEY") or self._load_api_key_from_env_file()

        if not api_key:
            answer_widget = self.query_one("#answer")
            answer_widget.update("⚠️  No API key found. Please enter your Gemini API key below.")
            answer_widget.add_class("error")

            # Focus the input and set a flag to indicate we're waiting for API key
            input_widget = self.query_one("#question", Input)
            input_widget.placeholder = "Paste your Gemini API key here and press Enter"
            input_widget.focus()
            self.waiting_for_api_key = True
            self.client = None
            return

        self.waiting_for_api_key = False
        try:
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.5-flash"
            self.current_response = None
            self.last_query = None
        except Exception as e:
            answer_widget = self.query_one("#answer")
            answer_widget.update(f"❌ Error initializing Gemini: {str(e)}")
            answer_widget.add_class("error")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        """Handle Enter to generate command or save API key"""
        query = message.value
        if not query:
            return

        # If we're waiting for API key, process it
        if hasattr(self, 'waiting_for_api_key') and self.waiting_for_api_key:
            await self._setup_api_key(query)
            return

        await self.generate_command(query)

    async def _setup_api_key(self, api_key: str) -> None:
        """Setup and validate the API key"""
        answer_widget = self.query_one("#answer")
        input_widget = self.query_one("#question", Input)

        answer_widget.update("🔑 Validating API key...")
        answer_widget.remove_class("error")
        answer_widget.add_class("loading")

        try:
            # Try to initialize the client with the provided API key
            self.client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.5-flash"
            self.current_response = None
            self.last_query = None

            # Save the API key to .env file
            self._save_api_key_to_env_file(api_key)

            answer_widget.update("✓ API key saved successfully! You can now enter your commands.")
            answer_widget.remove_class("loading")
            answer_widget.add_class("success")

            # Reset the input placeholder
            input_widget.value = ""
            input_widget.placeholder = "> show pods that crashed in the last 30 minutes in prod"
            self.waiting_for_api_key = False

            self.notify("✓ API key configured successfully!", severity="information")

        except Exception as e:
            answer_widget.update(f"❌ Invalid API key: {str(e)}\nPlease try again.")
            answer_widget.remove_class("loading")
            answer_widget.add_class("error")
            input_widget.value = ""

    def action_unfocus_input(self) -> None:
        """Unfocus the input field when ESC is pressed"""
        input_widget = self.query_one("#question", Input)
        input_widget.blur()

    async def generate_command(self, query: str) -> None:
        """Generate command from natural language query"""
        # Check if client is initialized
        if not hasattr(self, 'client') or self.client is None:
            self.notify("❌ Gemini client not initialized. Check your API key.", severity="error")
            return

        answer_widget = self.query_one("#answer")
        explanation_widget = self.query_one("#explanation", Markdown)
        output_widget = self.query_one("#output")

        answer_widget.update("🤔 Thinking...")
        answer_widget.add_class("loading")
        answer_widget.remove_class("error")
        answer_widget.remove_class("success")
        explanation_widget.display = False
        output_widget.display = False

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

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
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

            self.current_response = data
            self.last_query = query

            answer_widget.update(f"✓ {data['command']}")
            answer_widget.remove_class("loading")
            answer_widget.add_class("success")

            # Automatically copy to clipboard
            pyperclip.copy(data['command'])
            self.notify("✓ Command generated and copied to clipboard!", severity="information")

        except json.JSONDecodeError as e:
            answer_widget.update(f"❌ Error parsing response: {str(e)}\nRaw response: {text[:200]}")
            answer_widget.remove_class("loading")
            answer_widget.add_class("error")
        except Exception as e:
            answer_widget.update(f"❌ Error: {str(e)}")
            answer_widget.remove_class("loading")
            answer_widget.add_class("error")

    async def action_explain_command(self) -> None:
        """Show detailed explanation with loading animation"""
        explanation_widget = self.query_one("#explanation", Markdown)

        # Toggle if already showing
        if explanation_widget.display:
            explanation_widget.display = False
            return

        if not self.current_response or "detailed_explanation" not in self.current_response:
            self.notify("⚠️  No command to explain.", severity="warning")
            return

        # Show loading animation for ~1 second
        explanation_widget.display = True
        loading_frames = [
            "🤔 Thinking",
            "🧠 Processing",
            "⚙️ Working",
            "✨ Almost there..."
        ]

        for i in range(4):  # 4 frames * 0.25s = 1 second
            await explanation_widget.update(loading_frames[i % len(loading_frames)])
            await asyncio.sleep(0.25)

        # Show the detailed explanation with markdown rendering
        detailed = self.current_response["detailed_explanation"]
        await explanation_widget.update(f"# 📖 Detailed Explanation\n\n{detailed}")


if __name__ == "__main__":
    WTF().run()
