#!/usr/bin/env python3
"""
MeTTaClaw Runner

Usage:
    python run.py [script.metta]
    
Environment variables:
    OPENAI_API_KEY=...      # For OpenAI
    ANTHROPIC_API_KEY=...   # For Anthropic
    OLLAMA_API_BASE=...     # For Ollama (local)
    LLM_PROVIDER=...        # Explicit provider selection
    
Or create a .env file with your API keys.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import configuration loader
try:
    from mettaclaw_config import load_config, validate_config, print_config_summary
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("Warning: Configuration loader not available, using environment variables only")

# Load configuration
if CONFIG_AVAILABLE:
    config = load_config(project_root)
    
    # Print configuration summary if verbose
    if os.environ.get('METTACLAW_VERBOSE', '').lower() == 'true':
        print_config_summary(config)
    
    # Validate configuration
    is_valid, errors = validate_config(config)
    if not is_valid and not os.environ.get('METTACLAW_SKIP_VALIDATION'):
        print("Configuration validation warnings:")
        for error in errors:
            print(f"  - {error}")
        print("\nSet METTACLAW_SKIP_VALIDATION=true to skip validation")
        # Don't exit, allow running anyway

# Import PeTTa
try:
    from deps.PeTTa.python import petta
except ImportError as e:
    print(f"Error: Failed to import PeTTa: {e}")
    print("Make sure PeTTa is installed and in the deps/PeTTa directory")
    sys.exit(1)

# Import MeTTaClaw libraries
try:
    from lib_mettaclaw import *
except Exception as e:
    print(f"Warning: Failed to import some MeTTaClaw libraries: {e}")

def run_script(script_path: str = None):
    """Run a MeTTa script."""
    
    # Default to run.metta
    if script_path is None:
        script_path = project_root / 'run.metta'
    else:
        script_path = Path(script_path)
    
    if not script_path.exists():
        print(f"Error: Script not found: {script_path}")
        sys.exit(1)
    
    print(f"Running: {script_path}")
    
    # Initialize PeTTa
    p = petta.PeTTa(verbose=True)
    
    # Load the script
    try:
        result = p.load_metta_file(str(script_path))
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error running script: {e}")
        sys.exit(1)

if __name__ == '__main__':
    script = sys.argv[1] if len(sys.argv) > 1 else None
    run_script(script)
