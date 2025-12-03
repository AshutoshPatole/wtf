import os
from typing import Type

from textual._path import CSSPathType
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.driver import Driver
from textual.widgets import Header, Footer, Static, Input

from google import genai

class WTF(App):
    CSS = """
    Screen {
    align: center middle;
    }
    
    #main {
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
        border: solid yellow;
        padding: 1;
        display: none;
        margin-top: 1;
    }
    
    """

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(
            self,
            driver_class: Type[Driver] | None = None,
            css_path: CSSPathType | None = None,
            watch_css: bool = False,
            ansi_color: bool = False,
    ):
        super().__init__(driver_class, css_path, watch_css, ansi_color)
        self.model_name = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main") as container:
            yield Static("What command do you want to do?")
            yield Input(id="question", placeholder="find files less than 2kb", type="text", max_length=250)
            yield Static("", id="answer")
            yield Static("", id="explanation")
            yield Static(
                "💡 [Ctrl + Enter] Generate Command  |  [Enter] Run  |  [c] Copy  |  [e] Explain  |  [Ctrl + q] Quit",
                id="help-text", markup=False)

        yield Footer()

    def on_mount(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        answer_widget = self.query_one("#answer")
        if not api_key:
            answer_widget = self.query_one("#answer")
            answer_widget.update("❌ Error: GEMINI_API_KEY not found in environment variables.")
            answer_widget.add_class("error")
            return
        try:
            client = genai.Client(api_key=api_key)
            self.model_name = "gemini-2.5-flash"
            self.model = client.models.list()

        except Exception as e:
            answer_widget.update(f"❌ Error initializing Gemini: {str(e)}")
            answer_widget.add_class("error")



    def action_toggle_dark(self) -> None:
        self.theme = (
            'textual-dark' if self.theme == 'textual-light' else 'textual-light'
        )


if __name__ == "__main__":
    WTF().run()
