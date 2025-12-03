# Building WTF

This document explains how to build the WTF command generator application into standalone executables.

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

## Local Build

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Build with PyInstaller

```bash
pyinstaller wtf.spec
```

The executable will be created in the `dist/` directory:

- **Linux/macOS**: `dist/wtf`
- **Windows**: `dist/wtf.exe`

### 3. Run the Executable

```bash
# On Linux/macOS
./dist/wtf

# On Windows
.\dist\wtf.exe
```

## GitHub Actions (Automated Builds)

The repository includes a GitHub Actions workflow that automatically builds executables for all platforms.

### Trigger Builds

**On Push to Main:**

```bash
git push origin main
```

**On Pull Request:**

- Create a PR to `main` branch
- Builds will run automatically

**Manual Trigger:**

- Go to Actions tab in GitHub
- Select "Build Executables" workflow
- Click "Run workflow"

### Create a Release

To create a release with pre-built executables:

```bash
# Tag your commit
git tag v1.0.0
git push origin v1.0.0
```

This will:

1. Build executables for Windows, macOS, and Linux
2. Create a GitHub release
3. Attach all executables to the release

### Download Artifacts

For non-release builds, download artifacts from the Actions tab:

1. Go to Actions → Build Executables
2. Click on the workflow run
3. Scroll to "Artifacts" section
4. Download the executable for your platform

## Platform-Specific Notes

### Windows

- Executable: `wtf.exe`
- May trigger Windows Defender on first run (expected for unsigned executables)

### macOS

- Executable: `wtf`
- May need to allow in System Preferences → Security & Privacy
- Run `chmod +x wtf` to make executable

### Linux

- Executable: `wtf`
- Run `chmod +x wtf` to make executable
- Works on most modern Linux distributions

## Usage

After building or downloading the executable:

1. **First Run**: The app will prompt for your Gemini API key
2. **API Key Storage**: Saved to `.env` file in the same directory
3. **Generate Commands**: Type your natural language query and press Enter
4. **View Explanation**: Press `e` to see detailed explanation
5. **Quit**: Press `q` to exit

## Troubleshooting

### Build Fails

- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try cleaning the build: `rm -rf build dist` and rebuild

### Executable Won't Run

- **macOS/Linux**: Make sure it's executable: `chmod +x wtf`
- **Windows**: Right-click → Properties → Unblock

### Missing Dependencies

- PyInstaller should bundle all dependencies
- If issues persist, check the `wtf.spec` file for hidden imports
