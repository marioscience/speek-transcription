import logging
from pathlib import Path
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class STTEngine:
    ## Set device="cuda" for GPU, "cpu" for CPU
    def __init__(self, model_size="small", device="cuda"):
        logger.info(f"Attempting load of Whisper model '{model_size}' on device '{device}'...")

        #compute_type = "float16" if device == "cuda" else "int8"
        compute_type = "int8"

        try:
            logger.info(f"Loading Whisper model '{model_size}' on device '{device}'...")
            self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
            logger.info("Whisper model loaded successfully.")
            self.active_device = device
        except Exception as e:
            logger.error(f"GPU Initialization failed: {e}")
            logger.error("Falling back to CPU mode...")
            self.model = WhisperModel(model_size, device="cpu", compute_type=compute_type)
            self.active_device = "cpu"

        logger.info(f"Whisper model loaded on device '{self.active_device}'.")

    def transcribe(self, audio_path: Path):
        """
        Transcribes the audio file and returns the text.

        TODO:
        1 Call self.model.transcribe(str(audio_path), beam_size=5, ...)
        2 You MUST pass: vad_filter=True
        3 You MUST pass: vad_parameters=dict(min_silence_duration_ms=500)
        4 The transcribe method returns `segments` (a generator) and `info`
        5 Iterate through the `segments` generator, extract the `.text` property of each,
        join them with a space, and return the stripped string
        :param audio_path:
        :return:
        """
        segments, _ = self.model.transcribe(
            str(audio_path),
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        return " ".join(
            [segment.text for segment in segments]
        ).strip()