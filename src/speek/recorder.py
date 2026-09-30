import pyaudio
import wave
import threading
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, sample_rate=16000, max_seconds=120):
        self.sample_rate = sample_rate
        self.max_seconds = max_seconds
        self.chunk_size = 1024
        self.channels = 1
        self.format = pyaudio.paInt16

        self._pa = pyaudio.PyAudio()
        self._stream = None
        self._thread = None
        self._is_recording = False
        self._output_path = None
        self._output_path = None

    def start(self, output_path: Path, on_timeout=None) -> bool:
        """Starts recording audio, streaming directly to the disk"""
        if self._is_recording:
            logger.warning("Already recording")
            return False

        self._output_path = output_path
        self.on_timeout = on_timeout
        self._is_recording = True

        self._stream = self._pa.open(
            format=self.format,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=self.chunk_size
        )

        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> Path:
        """Stops recording and releases the stream."""
        self._is_recording = False
        if self._thread:
            self._thread.join()

        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
            self._stream = None

        return self._output_path

    def _record_loop(self):
        """
        TODO: Implement the bounded disk-streaming loop.

        1 Open self._output_path as a wave file ('wb').
        2 Set wave params: nchannels(self.channels),
        sampwidth(self._pa.get_sample_size(self.format)), framerate(self.sample_rate),
        3 Create a while loop that runs as long as self._is_recording is True.
        4 Inside the loop:
            a. Read `self.chunk_size` from `self._stream` using `exception_on_overflow=False`.
            b. Write the raw bytes to the wave file.
            c. Calculate total frames written. If (total_frames/self.sample_rate) >= self.max_seconds:
                set self._is_recording = False and break
        5 Outside the loop, make sure the wave file is closed!
        :return:
        """
        with wave.open(str(self._output_path), 'wb') as wf:

            # Set wave params
            wf.setnchannels(self.channels)
            wf.setsampwidth(self._pa.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)

            total_frames = 0

            # while loop recording is True
            while self._is_recording:
                # Read chunk from the mic
                data = self._stream.read(self.chunk_size, exception_on_overflow=False)

                # Write the raw bytes to disk
                wf.writeframes(data)

                # Enforce the time limit
                total_frames += self.chunk_size
                if (total_frames/self.sample_rate) >= self.max_seconds:
                    logger.warning("Max recording time reached. Auto-stopping")
                    self._is_recording = False
                    break


            if getattr(self, 'on_timeout', None) and (total_frames/self.sample_rate) >= self.max_seconds:
                logger.info("Max recording time reached. Auto-stopping")
                threading.Thread(target=self.on_timeout, daemon=True).start()