#!/usr/bin/env python3
import argparse
import os
import sys
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src.video_downloader import DriveVideoDownloader
from src.transcription import WhisperTranscriber
from src.cli import transcribe_media_outputs


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_credentials(client_secrets_path: str, token_path: str = "token.json") -> Credentials:
    creds: Optional[Credentials] = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds



def main(argv=None):
    p = argparse.ArgumentParser(description="Download a Google Drive video via OAuth user login.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file-id", help="Drive file ID of the video")
    src.add_argument("--url", help="Full Google Drive URL of the video")
    src.add_argument("--folder-id", help="Drive folder ID to process all video files inside")
    src.add_argument("--folder-url", help="Full Google Drive folder URL to process all video files inside")
    p.add_argument("-o", "--output", help="Output file path. Defaults to the Drive file name in CWD. In folder mode, ignored.")
    p.add_argument("--client-secrets", default=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "credentials.json"),
                   help="Path to OAuth Client secrets JSON (default: credentials.json or $GOOGLE_OAUTH_CLIENT_SECRETS)")
    p.add_argument("--token", default=os.environ.get("GOOGLE_OAUTH_TOKEN", "token.json"),
                   help="Path to store OAuth token (default: token.json or $GOOGLE_OAUTH_TOKEN)")
    p.add_argument("--force", action="store_true", help="Overwrite output file(s) if they exist")
    p.add_argument("--output-dir", default=os.path.join(os.getcwd(), "out"), help="Folder mode: directory to save all downloads (default: 'downloads' inside the current working directory)")
    # Transcription options
    p.add_argument("--transcribe", action="store_true", help="Transcribe the downloaded media with Whisper")
    p.add_argument("--whisper-model", default="small", help="Whisper model name (tiny/base/small/medium/large)")
    p.add_argument("--transcript-output", help="Path to write transcript .txt (defaults to video basename + .txt)")
    p.add_argument("--language", help="Language code for Whisper (optional)")
    p.add_argument("--srt", action="store_true", help="Also write an .srt subtitle file using Whisper segments")
    p.add_argument("--srt-output", help="Path to write .srt for single-file mode (defaults to video basename + .srt)")
    args = p.parse_args(argv)

    if not os.path.exists(args.client_secrets):
        print(f"Client secrets not found: {args.client_secrets}. See README for setup.", file=sys.stderr)
        return 2

    creds = get_credentials(args.client_secrets, token_path=args.token)
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

            if (args.transcribe or args.srt) and transcriber is not None:
                try:
                    transcribe_media_outputs(
                        out_path,
                        write_txt=args.transcribe,
                        write_srt=args.srt,
                        model=args.whisper_model,
                        language=args.language,
                        transcriber=transcriber,
                        display_name=name,
                    )
                except Exception as e:
                    print(f"Transcription/SRT failed for {name}: {e}", file=sys.stderr)
                    failures += 1

        return 1 if failures else 0

    # Single-file mode
    file_id_input = args.file_id or args.url
    file_id = DriveVideoDownloader.parse_drive_file_id(file_id_input)
    if not file_id:
        print("Could not parse a valid Drive file ID from input.", file=sys.stderr)
        return 2

    try:
        out_path = downloader.download(file_id, output=args.output, force=args.force)
        print(f"Downloaded to: {out_path}")
    except FileExistsError as e:
        print(str(e), file=sys.stderr)
        return 2

    if args.transcribe or args.srt:
        base, _ = os.path.splitext(out_path)
        transcript_path = args.transcript_output or f"{base}.txt"
        srt_path = args.srt_output or f"{base}.srt"
        try:
            transcribe_media_outputs(
                out_path,
                write_txt=args.transcribe,
                write_srt=args.srt,
                model=args.whisper_model,
                language=args.language,
                transcript_path=transcript_path,
                srt_path=srt_path,
            )
        except Exception as e:
            print(f"Transcription/SRT failed: {e}", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
