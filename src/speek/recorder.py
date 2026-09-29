import pyaudio
import wave
import threading
import tempfile
import logging

logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, device_index=None):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000 # Whisper prefers 16kHz
        self.device_index = device_index
        
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.is_recording = False
        self.stream = None
        self.thread = None
        
    def start_recording(self):
        self.frames = []
        self.is_recording = True
        
        # Determine effective device index, pyaudio sometimes dislikes explicit None
        kwargs = {
            'format': self.format,
            'channels': self.channels,
            'rate': self.rate,
            'input': True,
            'frames_per_buffer': self.chunk
        }
        if self.device_index is not None:
            kwargs['input_device_index'] = self.device_index

        self.stream = self.p.open(**kwargs)
        
        self.thread = threading.Thread(target=self._record_loop)
        self.thread.start()
        logger.info("Recording started...")
        
    def _record_loop(self):
        while self.is_recording:
            try:
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                self.frames.append(data)
            except Exception as e:
                logger.error(f"Error during recording: {e}")
                break

    def stop_recording(self) -> str:
        self.is_recording = False
        if self.thread:
            self.thread.join()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            
        logger.info("Recording stopped.")
        
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        wf = wave.open(temp_wav.name, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.p.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        
        return temp_wav.name

    def cleanup(self):
        self.p.terminate()
