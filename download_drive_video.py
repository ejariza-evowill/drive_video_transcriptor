#!/usr/bin/env python3
import argparse
import io
import os
import re
import sys
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


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


def parse_drive_file_id(s: str) -> Optional[str]:
    # If it's already an ID-like string (no slashes, modest length), accept
    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", s) and "/" not in s:
        return s

    # Common URL patterns
    patterns = [
        r"/file/d/([A-Za-z0-9_-]{10,})",  # https://drive.google.com/file/d/<id>/view
        r"[?&]id=([A-Za-z0-9_-]{10,})",   # https://drive.google.com/open?id=<id>
        r"/uc\?id=([A-Za-z0-9_-]{10,})", # https://drive.google.com/uc?id=<id>&export=download
        r"/drive/folders/([A-Za-z0-9_-]{10,})",  # folder link, not valid for video file
    ]
    for pat in patterns:
        m = re.search(pat, s)
        if m:
            return m.group(1)
    return None


def resolve_filename(service, file_id: str) -> (str, str):
    meta = service.files().get(fileId=file_id, fields="name,mimeType", supportsAllDrives=True).execute()
    return meta.get("name", file_id), meta.get("mimeType", "")


def is_video_mime(mime: str) -> bool:
    return mime.startswith("video/") or mime in {
        "application/vnd.google-apps.video"
    }


def download_file(service, file_id: str, dest_path: str):
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    try:
        while not done:
            status, done = downloader.next_chunk()
            if status:
                pct = int(status.progress() * 100)
                print(f"Downloading... {pct}%", end="\r", flush=True)
    finally:
        fh.close()
    print(f"\nSaved to {dest_path}")


def main(argv=None):
    p = argparse.ArgumentParser(description="Download a Google Drive video via OAuth user login.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--file-id", help="Drive file ID of the video")
    src.add_argument("--url", help="Full Google Drive URL of the video")
    p.add_argument("-o", "--output", help="Output file path. Defaults to the Drive file name in CWD")
    p.add_argument("--client-secrets", default=os.environ.get("GOOGLE_OAUTH_CLIENT_SECRETS", "credentials.json"),
                   help="Path to OAuth Client secrets JSON (default: credentials.json or $GOOGLE_OAUTH_CLIENT_SECRETS)")
    p.add_argument("--token", default=os.environ.get("GOOGLE_OAUTH_TOKEN", "token.json"),
                   help="Path to store OAuth token (default: token.json or $GOOGLE_OAUTH_TOKEN)")
    p.add_argument("--force", action="store_true", help="Overwrite output file if it exists")
    args = p.parse_args(argv)

    file_id_input = args.file_id or args.url
    file_id = parse_drive_file_id(file_id_input)
    if not file_id:
        print("Could not parse a valid Drive file ID from input.", file=sys.stderr)
        return 2

    if not os.path.exists(args.client_secrets):
        print(f"Client secrets not found: {args.client_secrets}. See README for setup.", file=sys.stderr)
        return 2

    creds = get_credentials(args.client_secrets, token_path=args.token)
    service = build("drive", "v3", credentials=creds)

    name, mime = resolve_filename(service, file_id)
    if not is_video_mime(mime):
        print(f"Warning: File mimeType '{mime}' does not look like a video.")

    out_path = args.output or os.path.abspath(name)
    if os.path.isdir(out_path):
        out_path = os.path.join(out_path, name)
    if os.path.exists(out_path) and not args.force:
        print(f"Refusing to overwrite existing file: {out_path}. Use --force to overwrite.", file=sys.stderr)
        return 2

    download_file(service, file_id, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

