# WTF - What The F\*\*\* Command Helper

A terminal-based UI tool that converts natural language queries into executable commands using Google's Gemini 2.5 Flash AI model.

## Features

- 🤖 **AI-Powered**: Uses Gemini 2.5 Flash for accurate command generation
- 🖥️ **OS-Aware**: Automatically generates commands for your operating system (Windows PowerShell or Linux Bash)
- 📋 **Copy to Clipboard**: One-key command copying
- 💡 **Explanations**: Toggle detailed explanations of what each command does

## Installation

1. Clone this repository
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Set your Gemini API key:

   ```bash
   # Linux/Mac
   export GEMINI_API_KEY="your-api-key-here"

   # Windows PowerShell
   $env:GEMINI_API_KEY="your-api-key-here"
   ```

## Usage

Run the application:

```bash
python main.py
```

Type your query in natural language and press Enter. For example:

- "show pods that crashed in the last 30 minutes in prod"
- "list all docker containers"
- "find files larger than 100MB"
- "show git commits from last week"

## Requirements

- Python 3.10+
- Gemini API key (get one at [Google AI Studio](https://makersuite.google.com/app/apikey))

## Dependencies

- `google-genai`: Gemini API client
- `pyperclip`: Clipboard functionality

## How It Works

1. You type a natural language query
2. The app detects your OS and shell
3. Gemini 2.5 Flash generates the appropriate command
4. The command is displayed and copied with an optional explanation

## License

MIT
