import io
import os
import re
from typing import Optional, Tuple

from googleapiclient.http import MediaIoBaseDownload


class DriveVideoDownloader:
    """Encapsulates Google Drive video download functionality.

    Provide an authenticated Drive API `service` (v3) to the constructor.
    The class exposes helpers to parse IDs, resolve filenames, and download
    the file to disk.
    """

    def __init__(self, service):
        self.service = service

    # --- Helpers -----------------------------------------------------------------
    @staticmethod
    def parse_drive_file_id(s: str) -> Optional[str]:
        """Extract a Drive file ID from a raw ID or common Drive URLs."""
        if re.fullmatch(r"[A-Za-z0-9_-]{10,}", s) and "/" not in s:
            return s

        patterns = [
            r"/file/d/([A-Za-z0-9_-]{10,})",  # https://drive.google.com/file/d/<id>/view
            r"[?&]id=([A-Za-z0-9_-]{10,})",   # https://drive.google.com/open?id=<id>
            r"/uc\?id=([A-Za-z0-9_-]{10,})", # https://drive.google.com/uc?id=<id>&export=download
            r"/drive/folders/([A-Za-z0-9_-]{10,})",  # folder link
        ]
        for pat in patterns:
            m = re.search(pat, s)
            if m:
                return m.group(1)
        return None

    @staticmethod
    def is_video_mime(mime: str) -> bool:
        return mime.startswith("video/") or mime in {"application/vnd.google-apps.video"}

    # --- Drive operations ---------------------------------------------------------
    def resolve_filename(self, file_id: str) -> Tuple[str, str]:
        meta = (
            self.service
            .files()
            .get(fileId=file_id, fields="name,mimeType", supportsAllDrives=True)
            .execute()
        )
        return meta.get("name", file_id), meta.get("mimeType", "")

    def download_file(self, file_id: str, dest_path: str) -> None:
        request = self.service.files().get_media(fileId=file_id, supportsAllDrives=True)
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

    # --- High-level API -----------------------------------------------------------
    def download(self, file_id_or_url: str, output: Optional[str] = None, *, force: bool = False) -> str:
        """Download a Drive video to `output` path.

        - Accepts a raw file ID or a Drive URL.
        - If `output` is a directory or None, uses the original Drive filename.
        - Returns the final output path on success.
        """
        file_id = self.parse_drive_file_id(file_id_or_url)
        if not file_id:
            raise ValueError("Could not parse a valid Drive file ID from input.")

        name, mime = self.resolve_filename(file_id)
        if not self.is_video_mime(mime):
            print(f"Warning: File mimeType '{mime}' does not look like a video.")

        out_path = output or os.path.abspath(name)
        if os.path.isdir(out_path):
            out_path = os.path.join(out_path, name)
        if os.path.exists(out_path) and not force:
            raise FileExistsError(
                f"Refusing to overwrite existing file: {out_path}. Use --force to overwrite."
            )

        self.download_file(file_id, out_path)
        return out_path

