import subprocess
import os
import logging

logger = logging.getLogger(__name__)

class OutputHandler:
    def handle(self, text: str):
        raise NotImplementedError

class TypeHandler(OutputHandler):
    def __init__(self):
        # Auto-detect Wayland vs X11
        session_type = os.environ.get("XDG_SESSION_TYPE", "x11")
        self.tool = "ydotool" if "wayland" in session_type.lower() else "xdotool"

    def handle(self, text: str):
        if not text:
            return
        logger.info(f"Typing text using {self.tool} in chunks...")

        """
        TODO: (Driver):
        If self.tool is "ydotool", run: ydotool type -- "text"
        If self.tool is "xdotool", run: xdotool type --clearmodifiers -- "text"
        
        Catch `subprocess.CalledProcessError` and `FileNotFoundError`
        and log them via logger.error() so the app doesn't crash if the tool is missing
        """
        chunk_size = 60
        if self.tool == "ydotool":
            try:
                for i in range(0, len(text), chunk_size):
                    subprocess.run(["ydotool", "type", "--", text[i:i+chunk_size]], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error typing text using ydotool: {e}")
            except FileNotFoundError as e:
                logger.error(f"ydotool not found: {e}")

        elif self.tool == "xdotool":
            try:
                for i in range(0, len(text), chunk_size):
                    subprocess.run(["xdotool", "type", "--clearmodifiers", "--", text[i:i+chunk_size]], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Error typing text using xdotool: {e}")
            except FileNotFoundError as e:
                logger.error(f"xdotool not found: {e}")
        else:
            logger.error(f"Unknown tool: {self.tool}")

class AntigravityCLIHandler(OutputHandler):
    def handle(self, text: str):
        if not text:
            return
        logger.info(f"Passing command to Antigravity CLI: {text}")
        """
        TODO (Driver):
        Run: agy -- "text"
        Catch `subprocess.CalledProcessError` and `FileNotFoundError`
        and log them via logger.error() so the app doesn't crash if the tool is missing
        """
        try:
            subprocess.run(["agy", "--", text], check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error passing command to Antigravity CLI: {e}")
        except FileNotFoundError as e:
            logger.error(f"agy not found: {e}")

def get_handler(mode_name: str) -> OutputHandler:
    mode_name = mode_name.lower().strip()
    if mode_name == "type":
        return TypeHandler()
    elif mode_name == "antigravity_cli":
        return AntigravityCLIHandler()
    else:
        logger.warning(f"Unknown mode '{mode_name}', falling back to 'type.")
        return TypeHandler()


