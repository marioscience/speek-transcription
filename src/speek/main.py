import sys
import logging
import threading
from pathlib import Path
from evdev import ecodes

from speek.state import StateMachine, AppState
from speek.recorder import AudioRecorder
from speek.stt import STTEngine
from speek.output import get_handler
from speek.hotkey import EvdevHotkeyListener

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def main():
    logger.info("Initializing Speek Voice Terminal...")

    state_machine = StateMachine()
    recorder = AudioRecorder(max_seconds=120)
    ## Change device to "cuda" for GPU, "cpu" for CPU
    stt = STTEngine(model_size="small", device="cuda")
    output_handler = get_handler("type")

    audio_path = Path("/tmp/speek_audio.wav")

    def process_audio():
        """Background thread to handle heavy ML inference and output"""
        try:
            logger.info("Transcribing...")
            text = stt.transcribe(audio_path)
            logger.info(f"Recognized: {text}")

            if text:
                # 1. Lock state to BUSY while executing
                state_machine.transition(AppState.TRANSCRIBING, AppState.BUSY)
                output_handler.handle(text)

        except Exception as e:
            logger.error(f"Error processing: {e}")
        finally:
            state_machine.force_reset()
            logger.info("Resetting state machine... Ready for next input.")

    def on_toggle():
        """
        TODO (Driver): Implement the atomic State Machine transitions!

        1. Try to transition from IDLE -> RECORDING.
           If True: Call `recorder.start(audio_path)` and return.

        2. Try to transition from RECORDING -> TRANSCRIBING.
           If True: Call `recorder.stop()`. Then spawn a `threading.Thread` targeting
           `process_audio` and `start()` it. Return.

        3. If neither transition succeeds, it means the system is BUSY or in an invalid state.
           Just log a warning and do nothing!
        :return:
        """
        if state_machine.transition(AppState.IDLE, AppState.RECORDING):
            recorder.start(audio_path, on_timeout=on_toggle)
            return

        if state_machine.transition(AppState.RECORDING, AppState.TRANSCRIBING):
            recorder.stop()
            threading.Thread(target=process_audio).start()
            return

        logger.warning("Invalid state transition!")


    target_keys = [ecodes.KEY_LEFTCTRL, ecodes.KEY_LEFTALT, ecodes.KEY_V]
    listener = EvdevHotkeyListener(target_keys, on_toggle)

    logger.info("Starting hardware listener... Press Ctrl+Alt+V to toggle.")
    listener.start()

    try:
        # Keep main thread alive
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Exiting...")
        recorder.stop()
        listener.stop()
        sys.exit(0)

if __name__ == "__main__":
    main()
