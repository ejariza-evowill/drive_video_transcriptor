from . import transcribe_media_outputs
import logging
from src.transcription import WhisperTranscriber

import os

logger = logging.getLogger(__name__)



def download_and_transcribe(args, file_id, target_path, downloader, transcriber=None):
    """Download a single file by ID and optionally transcribe it.
    Returns (out_path, transcript_path, srt_path) or None on failure.
    """
    try:
        out_path = downloader.download(file_id, output=target_path, force=args.force)
        logger.info("Downloaded to: %s", out_path)
    except FileExistsError as e:
        logger.error("%s", e)
        return None
    except Exception as e:
        logger.error("Download failed: %s", e)
        return None

    transcript_path = None
    srt_path = None
    if args.transcribe or args.srt:
        base, _ = os.path.splitext(out_path)
        transcript_path = args.transcript_output or f"{base}.txt"
        srt_path = args.srt_output or f"{base}.srt"
        transcriber = transcriber or WhisperTranscriber(model=args.whisper_model)
        outcome = transcribe_media_outputs(
            out_path,
            file_id_or_url=file_id,
            downloader=downloader,
            transcriber=transcriber,
            display_name=os.path.basename(out_path),
            transcript_path=transcript_path,
            srt_path=srt_path,
            args=args,
        )
        if isinstance(outcome, dict) and outcome.get("error"):
            logger.error("Transcription/SRT failed: %s", outcome["error"])
            return None
        transcript_path = outcome.get("transcript_path")
        srt_path = outcome.get("srt_path")
    return out_path, transcript_path, srt_path