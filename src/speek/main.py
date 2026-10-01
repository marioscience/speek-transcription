import sys
import logging
import threading
import queue
from pathlib import Path
from evdev import ecodes
from PyQt6.QtWidgets import QApplication

from speek.state import StateMachine, AppState
from speek.recorder import AudioRecorder
from speek.stt import STTEngine
from speek.output import get_handler
from speek.hotkey import EvdevHotkeyListener
from speek.gui import SpeekWindow, BackendSignals

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Initializing Speek Desktop Application...")

    # 1. Initialize the GUI Application BEFORE anything else
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False) # Prevent the daemon from dying when window hides
    signals = BackendSignals()
    window = SpeekWindow(signals)

    # Start hidden in the background, waiting for the hotkey
    window.hide()

    state_machine = StateMachine()
    recorder = AudioRecorder()
    stt = STTEngine(model_size="small", device="cuda")
    output_handler = get_handler("type")

    audio_queue = queue.Queue()
    output_dir = Path("/tmp")

    # Garbage Collect any orphaned chunks from previous fatal crashes or hard terminations
    for old_chunk in output_dir.glob("speek_chunk_*.wav"):
        try:
            old_chunk.unlink()
        except OSError:
            pass

    # Dynamic Live-Swapping for the UI Button
    def on_ui_source_toggled(checked):
        # If the user clicks the button WHILE the app is already recording, hot-swap the hardware stream!
        if getattr(recorder, "_is_recording", False):
            logger.info("Live hot-swapping audio source!")
            recorder.stop()
            new_mode = "mic" if checked else "desktop"
            recorder.start(output_dir, audio_queue, source_mode=new_mode)

    window.btn_source.toggled.connect(on_ui_source_toggled)

    def transcription_worker():
        """Permanent background thread that eats chunks from the Queue"""
        logger.info("AI Consumer Thread started. Waiting for chunks...")
        while True:
            chunk_path = audio_queue.get()

            try:
                # 1. Thread-safe check of the GUI state
                current_task = "translate" if window.is_translate_enabled else "transcribe"
                
                # 2. Transcribe or Translate the audio chunk
                text = stt.transcribe(chunk_path, task=current_task)

                if text:
                    logger.info(f"Recognized: {text}")
                    # Safely securely send text to the GUI Thread via our Signal
                    signals.new_transcription.emit(text)

                    # Check thread-safe Machine Gun state
                    if window.is_machine_gun_enabled:
                        output_handler.handle(text)

            except Exception as e:
                logger.error(f"Error processing chunk {chunk_path}: {e}")
            finally:
                audio_queue.task_done()
                if chunk_path.exists():
                    chunk_path.unlink()

    # Spawn the permanent consumer thread
    consumer_thread = threading.Thread(target=transcription_worker, daemon=True)
    consumer_thread.start()

    def on_toggle():
        """Handles the Hotkey logic for the Microphone and GUI Visibility"""
        if state_machine.transition(AppState.IDLE, AppState.RECORDING):
            logger.info("Microphone HOT.")
            signals.show_window.emit()  # Safely trigger GUI show from main thread
            
            source_mode = "mic" if window.is_mic_enabled else "desktop"
            recorder.start(output_dir, audio_queue, source_mode=source_mode)
            return

        if state_machine.transition(AppState.RECORDING, AppState.IDLE):
            logger.info("Microphone COLD.")
            recorder.stop()
            signals.hide_window.emit()  # Safely trigger GUI hide from main thread
            return

        logger.warning("Invalid state transition!")

    target_keys = [ecodes.KEY_LEFTCTRL, ecodes.KEY_LEFTALT, ecodes.KEY_V]
    listener = EvdevHotkeyListener(target_keys, on_toggle)
    listener.start()

    logger.info("Speek is ready. Press Ctrl+Alt+V to begin.")

    # 2. Hand over the Main Thread to the PyQt Event Loop!
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        logger.info("Exiting...")
        recorder.stop()
        listener.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
