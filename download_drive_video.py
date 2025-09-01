#!/usr/bin/env python3
import os
import sys

from googleapiclient.discovery import build
from src.auth import get_credentials, DEFAULT_SCOPES
from src.video_downloader import DriveVideoDownloader
from src.transcription import WhisperTranscriber
from src.cli import transcribe_media_outputs, build_arg_parser


def main(argv=None):
    p = build_arg_parser()
    args = p.parse_args(argv)

    if not os.path.exists(args.client_secrets):
        print(f"Client secrets not found: {args.client_secrets}. See README for setup.", file=sys.stderr)
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
            print(f"Failed to list folder contents: {e}", file=sys.stderr)
            return 2

        if not videos:
            print("No video files found in the specified folder.")
            return 0

        out_dir = args.output_dir or os.getcwd()
        os.makedirs(out_dir, exist_ok=True)
        if args.transcript_output:
            print("Note: --transcript-output is ignored in folder mode; saving next to each video.")

        transcriber = None
        if args.transcribe or args.srt:
            transcriber = WhisperTranscriber(model=args.whisper_model)

        failures = 0
        for f in videos:
            vid = f.get("id")
            name = f.get("name") or f"{vid}.mp4"
            dest_path = os.path.join(out_dir, name)
            try:
                out_path = downloader.download(vid, output=dest_path, force=args.force)
                print(f"Downloaded to: {out_path}")
            except FileExistsError as e:
                print(str(e), file=sys.stderr)
                # Skip if not forcing
                if not args.force:
                    continue
                else:
                    failures += 1
                    continue
            except Exception as e:
                print(f"Download failed for {name}: {e}", file=sys.stderr)
                failures += 1
                continue

            if args.transcribe or args.srt:
                # In folder mode, ignore global --transcript-output/--srt-output and
                # write next to each video file by default.
                base, _ = os.path.splitext(out_path)
                transcript_path = f"{base}.txt"
                srt_path = f"{base}.srt"
                outcome = transcribe_media_outputs(
                    out_path,
                    file_meta=f,
                    transcriber=transcriber,
                    display_name=name,
                    transcript_path=transcript_path,
                    srt_path=srt_path,
                    args=args,
                )
                if isinstance(outcome, dict) and outcome.get("error"):
                    print(f"Transcription/SRT failed for {name}: {outcome['error']}", file=sys.stderr)
                    failures += 1

        return 1 if failures else 0

    # Single-file mode
    file_id_input = args.file_id or args.url
    file_id = DriveVideoDownloader.parse_drive_file_id(file_id_input)
    if not file_id:
        print("Could not parse a valid Drive file ID from input.", file=sys.stderr)
        return 2

    # Determine destination path for single file, honoring --output-dir
    try:
        base_name, _ = downloader.resolve_filename(file_id)
    except Exception as e:
        print(f"Failed to resolve filename: {e}", file=sys.stderr)
        return 2

    if args.output:
        target_path = args.output
    else:
        os.makedirs(args.output_dir, exist_ok=True)
        target_path = os.path.join(args.output_dir, base_name)

    try:
        out_path = downloader.download(file_id, output=target_path, force=args.force)
        print(f"Downloaded to: {out_path}")
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        return 2

    if args.transcribe or args.srt:
        base, _ = os.path.splitext(out_path)
        transcript_path = args.transcript_output or f"{base}.txt"
        srt_path = args.srt_output or f"{base}.srt"
        # Build SRT header from file metadata
        outcome = transcribe_media_outputs(
            out_path,
            file_id_or_url=file_id,
            downloader=downloader,
            args=args,
        )
        if isinstance(outcome, dict) and outcome.get("error"):
            print(f"Transcription/SRT failed: {outcome['error']}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
