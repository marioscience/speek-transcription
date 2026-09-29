from pynput import keyboard
import logging

logger = logging.getLogger(__name__)

class HotkeyToggleListener:
    def __init__(self, hotkey_str, on_toggle_callback):
        self.hotkey_str = hotkey_str
        self.on_toggle_callback = on_toggle_callback
        
    def _on_activate(self):
        logger.debug(f"Hotkey {self.hotkey_str} activated.")
        self.on_toggle_callback()

    def start(self):
        self.listener = keyboard.GlobalHotKeys({
            self.hotkey_str: self._on_activate
        })
        self.listener.start()
        
    def stop(self):
        if hasattr(self, 'listener'):
            self.listener.stop()
