import os
import json
import shutil
from pathlib import Path

def get_mcp_config():
    # Get the absolute path of the project root (one level up from src/)
    project_root = Path(__file__).parent.parent.absolute()
    
    # Check if 'uv' is installed
    uv_path = shutil.which("uv")
    
    if uv_path:
        # Configuration using 'uv' (Recommended)
        config = {
            "docs-forai": {
                "command": "uv",
                "args": [
                    "--directory",
                    str(project_root),
                    "run",
                    "serve"
                ],
                "disabled": False
            }
        }
        method = "UV (Recommended)"
    else:
        # Fallback to standard python if uv is not found
        # Assumes a 'venv' folder exists in the project root
        python_exe = "python"
        if os.name == "nt": # Windows
            python_exe = str(project_root / "venv" / "Scripts" / "python.exe")
        else: # Linux/macOS
            python_exe = str(project_root / "venv" / "bin" / "python")
            
        config = {
            "docs-forai": {
                "command": python_exe,
                "args": [
                    str(project_root / "src" / "mcp_server.py")
                ],
                "disabled": False
            }
        }
        method = "Standard Python (Venv)"

    print("\n" + "="*60)
    print(f"Docs-ForAI MCP Configuration Snippet ({method})")
    print("="*60)
    print("\nCopy and paste the following block into your 'mcp_config.json' file:")
    print("\n" + json.dumps(config, indent=2))
    print("\n" + "="*60)
    print("Note: If you haven't installed dependencies yet, run 'uv run setup'")
    print("="*60 + "\n")

if __name__ == "__main__":
    get_mcp_config()
