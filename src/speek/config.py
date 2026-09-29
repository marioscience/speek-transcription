import tomllib
import os
import sys
from pathlib import Path

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "voice-terminal" / "config.toml"

DEFAULT_CONFIG_CONTENT = """
[general]
# Output mode: "type" or "antigravity_cli"
mode = "type"

[hotkey]
# The combination to press to toggle recording on and off
keys = "<ctrl>+<alt>+v"

[whisper]
# Model size: tiny, base, small, medium, large-v2, large-v3
model_size = "small"
device = "cuda"

[audio]
# None means default. Set to integer index of your mic if known.
device_index = null
"""

def load_config():
    if not DEFAULT_CONFIG_PATH.exists():
        DEFAULT_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DEFAULT_CONFIG_PATH, "w") as f:
            f.write(DEFAULT_CONFIG_CONTENT)
        print(f"Created default config at {DEFAULT_CONFIG_PATH}")
    
    try:
        with open(DEFAULT_CONFIG_PATH, "rb") as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Error loading config from {DEFAULT_CONFIG_PATH}: {e}")
        sys.exit(1)
