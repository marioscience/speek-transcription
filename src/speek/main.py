import sys
import logging
import argparse
import os
import time
import threading

from speek.config import load_config
from speek.recorder import AudioRecorder
from speek.stt import STTEngine
from speek.hotkey import HotkeyToggleListener
from speek.output import get_handler

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

def main():
    parser = argparse.ArgumentParser(description="Speek - Voice Terminal")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--mode", type=str, help="Override output mode (e.g. type, antigravity_cli)")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    # Load config
    cfg = load_config()
    
    mode = args.mode if args.mode else cfg.get("general", {}).get("mode", "type")
    hotkey_str = cfg.get("hotkey", {}).get("keys", "<ctrl>+<alt>+v")
    model_size = cfg.get("whisper", {}).get("model_size", "small")
    device = cfg.get("whisper", {}).get("device", "cuda")
    device_idx = cfg.get("audio", {}).get("device_index", None)

    # Initialize components
    recorder = AudioRecorder(device_index=device_idx)
    stt = STTEngine(model_size=model_size, device=device)
    handler = get_handler(mode)

    print(f"\n[Speek is Ready] Mode: {mode.upper()} | Hotkey: {hotkey_str}")
    print(f"Press {hotkey_str} to start/stop recording. Press Ctrl+C in this terminal to exit.\n")

    state = {"is_recording": False}

    def on_toggle():
        if state["is_recording"]:
            print("\n[Speek] Stopping recording...")
            state["is_recording"] = False
            audio_file = recorder.stop_recording()
            
            def process_audio():
                try:
                    print("[Speek] Transcribing...")
                    text = stt.transcribe(audio_file)
                    print(f"[Speek] Transcript: {text}")
                    if text:
                        handler.handle(text)
                    else:
                        print("[Speek] No speech detected.")
                except Exception as e:
                    logger.error(f"Error during processing: {e}")
                finally:
                    if os.path.exists(audio_file):
                        os.remove(audio_file)
                print(f"\n[Speek] Listening for hotkey {hotkey_str}...")
                
            threading.Thread(target=process_audio).start()
        else:
            print("\n[Speek] Recording started... Speak now!")
            state["is_recording"] = True
            recorder.start_recording()

    listener = HotkeyToggleListener(hotkey_str, on_toggle)
    listener.start()

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nExiting Speek...")
        if state["is_recording"]:
            recorder.stop_recording()
        listener.stop()
        recorder.cleanup()
        sys.exit(0)

if __name__ == "__main__":
    main()
