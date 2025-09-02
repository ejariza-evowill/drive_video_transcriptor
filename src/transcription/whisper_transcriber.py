import os
import shutil
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

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
        allowed_languages: Optional[List[str]] = None,
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

        chosen_lang = language
        # If a set of allowed languages is provided and no explicit language was given,
        # detect language and choose the best within the allowed set.
        if chosen_lang is None and allowed_languages:
            try:
                import whisper
                import torch
                from whisper.audio import N_FRAMES, N_SAMPLES
                # Normalize codes to lowercase
                allowed = [str(x).lower() for x in allowed_languages if str(x).strip()]
                if allowed:
                    logger.info(
                        "Detecting language, will restrict to allowed set: %s", ", ".join(allowed)
                    )
                    audio = whisper.load_audio(media_path)
                    audio = whisper.pad_or_trim(audio, N_SAMPLES) # type: ignore
                    dtype = torch.float16
                    mel = whisper.log_mel_spectrogram(audio, model.dims.n_mels, padding=N_SAMPLES)
                    mel_segment = whisper.pad_or_trim(mel, N_FRAMES).to(model.device).to(dtype)
                    logger.info("Detecting language...")
                    _, probs = model.detect_language(mel_segment)
                    # Pick the highest probability among the allowed set
                    chosen_lang = max(allowed, key=lambda l: float(probs.get(l, 0.0)))
                    logger.info("Detected language: %s", chosen_lang)               
            except Exception:
                # Fall back to default detection if anything goes wrong
                chosen_lang = None

        result = model.transcribe(
            media_path, language=chosen_lang, task=task, verbose=verbose
        )
        return result

    # --- SRT helpers -------------------------------------------------------------
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        if seconds < 0:
            seconds = 0
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int(round((seconds - int(seconds)) * 1000))
        # handle 60th-second rounding overflow
        if millis == 1000:
            millis = 0
            secs += 1
            if secs == 60:
                secs = 0
                mins += 1
                if mins == 60:
                    mins = 0
                    hrs += 1
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    @classmethod
    def segments_to_srt(cls, segments: List[Dict[str, Any]]) -> str:
        """Convert Whisper segments to SRT string."""
        lines: List[str] = []
        for i, seg in enumerate(segments, start=1):
            start = cls._format_timestamp(float(seg.get("start", 0.0)))
            end = cls._format_timestamp(float(seg.get("end", 0.0)))
            text = (seg.get("text") or "").strip()
            lines.append(str(i))
            lines.append(f"{start} --> {end}")
            lines.append(text)
            lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    @classmethod
    def save_srt(
        cls,
        segments: List[Dict[str, Any]],
        out_path: str,
        header_comments: Optional[List[str]] = None,
    ) -> None:
        """Write segments to an .srt file at `out_path`.

        Optionally prepend comment lines (prefixed with '# ').
        """
        body = cls.segments_to_srt(segments)
        header = ""
        if header_comments:
            commented = [f"# {str(line).strip()}" for line in header_comments if str(line).strip()]
            if commented:
                header = "\n".join(commented) + "\n\n"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(header)
            f.write(body)
