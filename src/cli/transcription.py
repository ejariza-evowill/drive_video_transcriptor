import os
from typing import Optional, Dict, Any, List

from src.transcription import WhisperTranscriber


def build_srt_header_comments_from_dict(meta: Dict[str, Any]) -> list:
    """Build SRT header comment lines from a Drive file metadata dict.

    Expects keys like 'ownerDisplayName' and 'modifiedTime'. Missing/blank
    values are omitted. Returns a list of comment lines without the '# ' prefix.
    """
    header: list = []
    owner = (meta.get("ownerDisplayName") or "").strip()
    modified = (meta.get("modifiedTime") or "").strip()
    if owner:
        header.append(f"Owner: {owner}")
    if modified:
        header.append(f"Modified: {modified}")
    return header


def build_srt_header_comments_from_file_id(source: str, *, downloader: Any) -> list:
    """Fetch metadata for `source` (file ID/URL) and build SRT header comments.

    Uses `downloader.get_video_metadata(id_or_url)` to obtain the dict, then
    delegates to `build_srt_header_comments_from_dict`.
    """
    if not downloader:
        raise ValueError("downloader is required to build headers from a file ID/URL")
    meta: Dict[str, Any] = downloader.get_video_metadata(source)
    return build_srt_header_comments_from_dict(meta)


# Note: no generic wrapper; use the typed helpers above directly.

def transcribe_media_outputs(
    media_path: str,
    *,
    write_txt: bool,
    write_srt: bool,
    model: str = "small",
    language: Optional[str] = None,
    transcript_path: Optional[str] = None,
    srt_path: Optional[str] = None,
    # Optionally supply SRT header data
    srt_header_comments: Optional[List[str]] = None,
    file_meta: Optional[Dict[str, Any]] = None,
    file_id_or_url: Optional[str] = None,
    downloader: Any = None,
    transcriber: Optional[WhisperTranscriber] = None,
    display_name: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Transcribe a media file and write .txt and/or .srt outputs.

    Returns a dict with keys: transcript_path, srt_path.
    Raises on failure from underlying transcription or file I/O.
    """
    if not (write_txt or write_srt):
        return {"transcript_path": None, "srt_path": None}

    base, _ = os.path.splitext(media_path)
    if transcript_path is None:
        transcript_path = f"{base}.txt"
    if srt_path is None:
        srt_path = f"{base}.srt"

    # Reuse provided transcriber if any, else create a new one
    local_transcriber = transcriber or WhisperTranscriber(model=model)

    label = f" '{display_name}'" if display_name else ""
    print(f"Transcribing{label} with Whisper model '{local_transcriber.model_name}'...")
    result: Dict[str, Any] = local_transcriber.transcribe(media_path, language=language)

    if write_txt:
        text = (result or {}).get("text", "").strip()
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Transcript saved to {transcript_path}")

    if write_srt:
        segments = (result or {}).get("segments", []) or []
        if segments:
            header_comments = srt_header_comments
            if header_comments is None:
                try:
                    if file_meta is not None:
                        header_comments = build_srt_header_comments_from_dict(file_meta)
                    elif file_id_or_url is not None and downloader is not None:
                        header_comments = build_srt_header_comments_from_file_id(
                            file_id_or_url, downloader=downloader
                        )
                except Exception:
                    header_comments = None
            WhisperTranscriber.save_srt(segments, srt_path, header_comments=header_comments)
            print(f"SRT saved to {srt_path}")
        else:
            raise RuntimeError("No segments found to write SRT.")

    return {"transcript_path": transcript_path if write_txt else None,
            "srt_path": srt_path if write_srt else None}
