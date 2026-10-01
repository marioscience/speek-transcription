import subprocess
import wave
import threading
import logging
import queue
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)


class AudioRecorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self.chunk_size = 1024
        self.channels = 1

        # VOX Configuration
        self.silence_threshold = 500  # Amplitude threshold.
        self.silence_limit_sec = 1.0  # How long you must pause before we slice
        self.min_chunk_seconds = 2.0  # Don't slice files smaller than 2 seconds
        self.max_chunk_seconds = 15.0 # Hard limit

        self._parec_proc = None
        self._thread = None
        self._is_recording = False
        self._output_dir = None
        self._queue = None

    def _get_hardware_mic(self):
        """Scans PipeWire/PulseAudio to find a physical microphone, bypassing misconfigured default settings"""
        import subprocess
        try:
            # 1. Check if the default source is already a hardware microphone
            default_source = subprocess.check_output(["pactl", "get-default-source"], text=True).strip()
            if not default_source.endswith(".monitor"):
                return default_source
                
            # 2. If default is a Monitor, scan the system for a real physical ALSA microphone
            sources = subprocess.check_output(["pactl", "list", "sources", "short"], text=True)
            for line in sources.splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    source_name = parts[1]
                    if not source_name.endswith(".monitor") and "input" in source_name.lower():
                        return source_name
        except Exception:
            pass
        return None

    def start(self, output_dir: Path, audio_queue: queue.Queue, source_mode: str = "mic") -> bool:
        if self._is_recording:
            return False

        self._output_dir = output_dir
        self._queue = audio_queue
        self._is_recording = True

        try:
            # Universal Linux Audio pipeline via parec!
            cmd = ["parec", "--format=s16le", "--rate=16000", "--channels=1"]
            
            import subprocess
            if source_mode == "desktop":
                sink = subprocess.check_output(["pactl", "get-default-sink"], text=True).strip()
                monitor = f"{sink}.monitor"
                cmd.extend(["-d", monitor])
                logger.info(f"Spawning parec for Desktop Monitor: {monitor}")
            else:
                # Force Hardware Microphone explicitly!
                mic_source = self._get_hardware_mic()
                if mic_source:
                    cmd.extend(["-d", mic_source])
                    logger.info(f"Spawning parec for Hardware Microphone: {mic_source}")
                else:
                    logger.info("Spawning parec for Default Source (No hardware mic found).")
                
            self._parec_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        except Exception as e:
            logger.error(f"Failed to spawn parec: {e}")
            self._is_recording = False
            return False

        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._is_recording = False

        # 1. Terminate streams FIRST to unblock the thread's read() calls!
        if self._parec_proc:
            self._parec_proc.terminate()

        # 2. NOW safely wait for the unblocked thread to exit
        if self._thread:
            self._thread.join()
            self._thread = None

        # 3. Final hardware cleanup
        if self._parec_proc:
            self._parec_proc.wait()
            self._parec_proc = None

    def _record_loop(self):
        chunk_index = 0
        chunk_duration_sec = self.chunk_size / self.sample_rate
        
        import time
        session_id = int(time.time() * 1000)

        while self._is_recording:
            chunk_path = self._output_dir / f"speek_chunk_{session_id}_{chunk_index}.wav"

            with wave.open(str(chunk_path), 'wb') as wf:
                wf.setnchannels(self.channels)
                # 16-bit PCM Audio is exactly 2 bytes per sample.
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)

                frames_written = 0
                silent_chunks = 0

                # Run until the hard max limit is reached, or stopped early
                while self._is_recording and frames_written < (self.max_chunk_seconds * self.sample_rate):
                    try:
                        if self._parec_proc:
                            data = self._parec_proc.stdout.read(self.chunk_size * 2)
                        else:
                            break
                            
                        if not data:
                            continue

                        wf.writeframes(data)
                        frames_written += self.chunk_size

                        # Calculate acoustic energy (Volume)
                        audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32)
                        rms_volume = np.sqrt(np.mean(np.square(audio_array)))

                        if rms_volume < self.silence_threshold:
                            silent_chunks += 1
                        else:
                            silent_chunks = 0  # Reset silence counter if you make noise

                        # Calculate current time states
                        current_duration = frames_written / self.sample_rate
                        silence_duration = silent_chunks * chunk_duration_sec

                        # Trigger dynamic slice if we hit our silence parameters
                        if silence_duration >= self.silence_limit_sec and current_duration >= self.min_chunk_seconds:
                            logger.info(f"Silence detected. Slicing chunk early at {current_duration:.1f}s.")
                            break

                    except Exception as e:
                        logger.error(f"Error reading audio stream: {e}")
                        break

            # Send finished chunk to the AI Queue
            if frames_written > 0:
                self._queue.put(chunk_path)

            chunk_index += 1