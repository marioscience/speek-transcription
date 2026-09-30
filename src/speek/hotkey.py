import evdev
from evdev import ecodes
import threading
import logging

logger = logging.getLogger(__name__)

class EvdevHotkeyListener:
    def __init__(self, target_keys: list[int], on_toggle_callback):
        """
        :param target_keys: A list of evdev ecodes, e.g.,
                [ecodes.KEY_LEFTCTRL, ecodes.KEY_LEFTALT, ecodes.KEY_LEFTSHIFT, ecodes.KEY_C]
        """
        self.target_keys = set(target_keys)
        self.on_toggle = on_toggle_callback
        self.is_running = False
        self.threads = []

    def start(self):
        self.is_running = True
        devices = [evdev.InputDevice(path) for path in evdev.list_devices()]

        for device in devices:
            capabilities = device.capabilities()
            if ecodes.EV_KEY in capabilities:
                # Start a dedicated thread for this hardware device
                t = threading.Thread(target=self._listen_device, args=(device,), daemon=True)
                self.threads.append(t)
                t.start()
                logger.info(f"Listening for hotkeys on {device.name}")

    def stop(self):
        self.is_running = False

    def _listen_device(self, device: evdev.InputDevice):
        """
        TODO (Driver):
        1. Iterate over `device.read_loop()`
        2. Filter for key press events. An event is a key press if:
           `event.type == ecodes.EV_KEY` AND `event.value == 1`
        3. If it is a key press, get the currently held keys using `device.active_keys()`
        4. Convert the active_keys list to a Python `set()`.
        5. If `self.target_keys` is a subset of the active keys (i.e. self.target_keys.issubset(active_keys_set)),
           the user has pressed our exact combo!
        6. Call `self.on_toggle()`

        Note: Wrap the loop in a try/except for OSError (if the keyboard is unplugged, the loop crashes).
        """
        try:
            for event in device.read_loop():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    active_keys_set = set(device.active_keys())
                    if self.target_keys.issubset(active_keys_set):
                        self.on_toggle()
        except OSError:
            logger.error(f"Keyboard unplugged: {device.name}")

