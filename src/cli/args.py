import argparse
import os


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Download a Google Drive video via OAuth user login.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file-id", help="Drive file ID of the video")
    src.add_argument("--url", help="Full Google Drive URL of the video")
    src.add_argument("--folder-id", help="Drive folder ID to process all video files inside")
    src.add_argument("--folder-url", help="Full Google Drive folder URL to process all video files inside")
    p.add_argument(
        "-o",
        "--output",
        help=(
            "Output file path. If omitted, the Drive filename is saved inside "
            "--output-dir. In folder mode, this flag is ignored."
        ),
    )
    p.add_argument(
        "--client-secrets",
        default=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "credentials.json"),
        help=(
            "Path to OAuth Client secrets JSON (default: credentials.json or "
            "$GOOGLE_OAUTH_CLIENT_SECRETS)"
        ),
    )
    p.add_argument(
        "--token",
        default=os.environ.get("GOOGLE_OAUTH_TOKEN", "token.json"),
        help=(
            "Path to store OAuth token (default: token.json or $GOOGLE_OAUTH_TOKEN)"
        ),
    )
    p.add_argument("--force", action="store_true", help="Overwrite output file(s) if they exist")
    p.add_argument(
        "--output-dir",
        default=os.path.join(os.getcwd(), "out"),
        help=(
            "Directory to save downloads. Used for folder mode and for single-file "
            "mode when --output is not provided (default: ./out)."
        ),
    )
    # Transcription options
    p.add_argument("--transcribe", action="store_true", help="Transcribe the downloaded media with Whisper")
    p.add_argument("--whisper-model", default="small", help="Whisper model name (tiny/base/small/medium/large)")
    p.add_argument("--transcript-output", help="Path to write transcript .txt (defaults to video basename + .txt)")
    p.add_argument("--language", help="Language code for Whisper (optional)")
    p.add_argument("--srt", action="store_true", help="Also write an .srt subtitle file using Whisper segments")
    p.add_argument("--srt-output", help="Path to write .srt for single-file mode (defaults to video basename + .srt)")
    return p
