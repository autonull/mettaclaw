#!/usr/bin/env python3
"""
MeTTaClaw Runner — runs MeTTa scripts via PeTTa.

Usage:
    python run.py [script.metta]

Environment:
    OPENAI_API_KEY=...      # OpenAI
    ANTHROPIC_API_KEY=...   # Anthropic
    OLLAMA_API_BASE=...     # Ollama local
    OLLAMA_MODEL=...        # Ollama model name

Or create a .env file with your keys.
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent

# Load .env if present (simple parser, no dependencies)
env_file = project_root / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("\"'")
            os.environ.setdefault(key, value)

# Import PeTTa
try:
    sys.path.insert(0, str(project_root / "deps" / "PeTTa" / "python"))
    from petta import PeTTa
except ImportError as e:
    print(f"Error: PeTTa not found at deps/PeTTa/python")
    print(f"Clone it with: git clone https://github.com/trueagi-io/PeTTa deps/PeTTa")
    print(f"Or use the container: ./run.sh build && ./run.sh run")
    print(f"Details: {e}")
    sys.exit(1)


def run_script(script_path=None):
    if script_path is None:
        script_path = project_root / "run.metta"
    else:
        script_path = Path(script_path)

    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)

    print(f"Running: {script_path}")
    p = PeTTa(verbose=True)

    try:
        result = p.load_metta_file(str(script_path))
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    script = sys.argv[1] if len(sys.argv) > 1 else None
    run_script(script)
