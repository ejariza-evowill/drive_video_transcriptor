#!/usr/bin/env python3
import os
import logging

from googleapiclient.discovery import build
from src.auth import get_credentials, DEFAULT_SCOPES
from src.video_downloader import DriveVideoDownloader
from src.transcription import WhisperTranscriber
from src.cli import build_arg_parser, download_and_transcribe


logger = logging.getLogger(__name__)

def main(argv=None):
    # Configure basic logging; adjust level via LOG_LEVEL env if desired
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    p = build_arg_parser()
    args = p.parse_args(argv)

    if not os.path.exists(args.client_secrets):
        logger.error(
            "Client secrets not found: %s. See README for setup.", args.client_secrets
        )
        return 2

    creds = get_credentials(args.client_secrets, token_path=args.token, scopes=DEFAULT_SCOPES)
    # Recreate service with valid creds (handles refresh or first auth)
    downloader = DriveVideoDownloader(build("drive", "v3", credentials=creds))

    # Folder mode
    if args.folder_id or args.folder_url:
        folder_input = args.folder_id or args.folder_url
        try:
            videos = downloader.list_folder_videos(folder_input)
        except Exception as e:
            logger.error("Failed to list folder contents: %s", e)
            return 2

        if not videos:
            logger.info("No video files found in the specified folder.")
            return 0

        out_dir = args.output_dir or os.getcwd()
        os.makedirs(out_dir, exist_ok=True)
        if args.transcript_output:
            logger.info(
                "Note: --transcript-output is ignored in folder mode; saving next to each video."
            )

        transcriber = None
        if args.transcribe or args.srt:
            transcriber = WhisperTranscriber(model=args.whisper_model)

        failures = 0
        for f in videos:
            file_id = f.get("id")
            file_name = f.get("name") or f"{file_id}.mp4"
            target_path = os.path.join(out_dir, file_name)

            response = download_and_transcribe(
                args, file_id, target_path, downloader, transcriber)
            
            if response is None:
                failures += 1
                continue

        return 1 if failures else 0

    # Single-file mode
    file_id_input = args.file_id or args.url
    file_id = DriveVideoDownloader.parse_drive_file_id(file_id_input)
    if not file_id:
        logger.error("Could not parse a valid Drive file ID from input.")
        return 2

    # Determine destination path for single file, honoring --output-dir
    try:
        base_name, _ = downloader.resolve_filename(file_id)
    except Exception as e:
        logger.error("Failed to resolve filename: %s", e)
        return 2

    if args.output:
        target_path = args.output
    else:
        os.makedirs(args.output_dir, exist_ok=True)
        target_path = os.path.join(args.output_dir, base_name)

    transcriber = None
    if args.transcribe or args.srt:
        transcriber = WhisperTranscriber(model=args.whisper_model)

    response = download_and_transcribe(args, file_id, target_path, downloader, transcriber)
    if response is None:
        return 2    
    out_path, transcript_path, srt_path = response

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
