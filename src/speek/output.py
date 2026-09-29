import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class OutputHandler:
    def handle(self, text: str):
        raise NotImplementedError

class TypeHandler(OutputHandler):
    def __init__(self):
        # Auto-detect session type (Wayland vs X11)
        session_type = os.environ.get("XDG_SESSION_TYPE", "x11")
        self.tool = "ydotool" if "wayland" in session_type.lower() else "xdotool"
        
    def handle(self, text: str):
        if not text:
            return
        logger.info(f"Typing text using {self.tool}: {text}")
        try:
            if self.tool == "ydotool":
                subprocess.run(["ydotool", "type", text], check=True)
            else:
                subprocess.run(["xdotool", "type", "--clearmodifiers", text], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to execute {self.tool}: {e}")
        except FileNotFoundError:
            logger.error(f"{self.tool} is not installed.")

class AntigravityCLIHandler(OutputHandler):
    def handle(self, text: str):
        if not text:
            return
        logger.info(f"Piping to agy: {text}")
        try:
            subprocess.run(["agy", text])
        except FileNotFoundError:
            logger.error("Antigravity CLI (agy) is not found in PATH.")

def get_handler(mode_name: str) -> OutputHandler:
    mode_name = mode_name.lower().strip()
    if mode_name == "type":
        return TypeHandler()
    elif mode_name == "antigravity_cli":
        return AntigravityCLIHandler()
    else:
        logger.warning(f"Unknown mode '{mode_name}', falling back to 'type'.")
        return TypeHandler()
