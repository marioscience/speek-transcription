import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class STTEngine:
    def __init__(self, model_size="small", device="cuda"):
        logger.info(f"Loading Whisper model '{model_size}' on '{device}'...")
        compute_type = "float16" if device == "cuda" else "int8"
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        logger.info("Model loaded successfully.")

    def transcribe(self, audio_path: str) -> str:
        logger.info("Transcribing audio...")
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
