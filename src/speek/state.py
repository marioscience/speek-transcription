import threading
import logging
from enum import Enum, auto

logger = logging.getLogger(__name__)

class AppState(Enum):
    IDLE = auto()
    RECORDING = auto()
    TRANSCRIBING = auto()
    BUSY = auto()

class StateMachine:
    """
    Thread-safe state manager for the speek application.
    Enforces a single state at a time and provides methods to transition between states.
    Atomic transitions to prevent race conditions and GPU OOMs.
    """
    def __init__(self):
        self._state = AppState.IDLE
        self._lock = threading.Lock()  # Describe: This lock ensures that only one thread can modify the state at a time, preventing race conditions.

    @property
    def current(self) -> AppState:
        with self._lock:
            return self._state

    def transition(self, expected_current: AppState, new_state: AppState) -> bool:
        """
        Attempts to atomically transition from `expected_current` to `new_state`.

        1. Acquire the lock.
        2. Check if self._state == expected_current.
        3. If true, update self._state and return True.
        4. If false, log a warning about an invalid transition and return False.
        :param expected_current:
        :param new_state:
        :return:
        """

        with self._lock:
            if self._state == expected_current:
                self._state = new_state
                return True
            else:
                logger.warning(f"Invalid state transition from {expected_current} to {new_state}.")
                return False


    def force_reset(self):
        """Emergency reset to IDLE, releasing all resources."""
        with self._lock:
            self._state = AppState.IDLE
            logger.warning("State machine forcefully reset to IDLE.")