from . import transcribe_media_outputs
from .transcription import read_srt_header_info
import logging
from src.transcription import WhisperTranscriber

import os

logger = logging.getLogger(__name__)


def download_and_transcribe(args, file_id, target_path, downloader, transcriber=None):
    """Download a single file by ID and optionally transcribe it.
    Returns (out_path, transcript_path, srt_path) or None on failure.
    """
    # Optimization: if user asked for transcription/SRT, and an existing .srt
    # with matching headers (Owner + Modified) is present for this video name,
    # skip both download and transcription work.
    if args.transcribe or args.srt:
        base, _ = os.path.splitext(target_path)
        existing_srt = f"{base}.srt"
        if os.path.exists(existing_srt):
            try:
                # Compare against current Drive metadata
                meta = downloader.get_video_metadata(file_id)
                owner = (meta.get("ownerDisplayName") or "").strip()
                modified = (meta.get("modifiedTime") or "").strip()
                header_info = read_srt_header_info(existing_srt)
                if (
                    header_info.get("Owner", "") == owner
                    and header_info.get("Modified", "") == modified
                ):
                    logger.info(
                        "Skipping download/transcription for '%s' (matching SRT found).",
                        os.path.basename(target_path),
                    )
                    # Return paths to indicate success without work
                    return target_path, None, existing_srt
            except Exception as e:
                logger.debug("SRT skip check failed, proceeding: %s", e)
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
            write_txt=False,
        )
        if isinstance(outcome, dict) and outcome.get("error"):
            logger.error("Transcription/SRT failed: %s", outcome["error"])
            return None
        transcript_path = outcome.get("transcript_path")
        srt_path = outcome.get("srt_path")
    return out_path, transcript_path, srt_path
