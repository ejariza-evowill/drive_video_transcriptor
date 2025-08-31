import os
import shutil
from typing import Optional, Dict, Any


class WhisperTranscriber:
    """Thin wrapper around OpenAI Whisper for local transcription.

    Requires `openai-whisper` Python package and `ffmpeg` installed on the system.
    """

    def __init__(self, model: str = "small"):
        self.model_name = model
        self._model = None

    def _ensure_deps(self) -> None:
        if not shutil.which("ffmpeg"):
            raise RuntimeError("ffmpeg not found in PATH. Please install ffmpeg.")
        # Lazy import so that users who don't need transcription don't need the dep
        try:
            import whisper  # noqa: F401
        except Exception as e:
            raise RuntimeError(
                "Python package 'openai-whisper' is not installed. Run: pip install -r requirements.txt"
            ) from e

    def _load_model(self):
        if self._model is None:
            import whisper
            self._model = whisper.load_model(self.model_name)
        return self._model

    def transcribe(
        self,
        media_path: str,
        *,
        language: Optional[str] = None,
        task: str = "transcribe",
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Transcribe the given audio/video file.

        Returns Whisper's full result dict; `result['text']` contains the transcript.
        """
        if not os.path.exists(media_path):
            raise FileNotFoundError(media_path)
        self._ensure_deps()
        model = self._load_model()
        result = model.transcribe(media_path, language=language, task=task, verbose=verbose)
        return result

