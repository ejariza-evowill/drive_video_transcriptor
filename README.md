**Google Drive Video Downloader**
- Purpose: Download a Google Drive video using your own account via OAuth login.

**Features**
- OAuth 2.0 user login (Installed app flow).
- Downloads with your permissions (no service account).
- Accepts a Drive file ID or full URL.
- Saves and reuses token in `token.json`.
 - Optional Whisper transcription after download.

**Prerequisites**
- Python 3.9+
- A Google Cloud project with Drive API enabled.
- An OAuth 2.0 Client ID for Desktop app.
 - For transcription: `ffmpeg` installed on your system and Python package `openai-whisper` (in requirements). Whisper also requires PyTorch; see notes below.

**Setup**
- Enable API: In Google Cloud Console, enable "Google Drive API" for your project.
- OAuth consent: Configure the OAuth consent screen for your project.
- Create credentials: Create OAuth Client ID of type "Desktop app" and download the JSON.
- Save the JSON as `credentials.json` at the project root (or set `GOOGLE_OAUTH_CLIENT_SECRETS`).
- Install dependencies: `pip install -r requirements.txt`

**Usage**
- Download by URL:
  - `python download_drive_video.py --url "https://drive.google.com/file/d/FILE_ID/view"`
- Download by ID:
  - `python download_drive_video.py --file-id FILE_ID`
- Download all videos from a Drive folder:
  - `python download_drive_video.py --folder-url "https://drive.google.com/drive/folders/FOLDER_ID" --output-dir /path/to/save`
  - or by ID: `python download_drive_video.py --folder-id FOLDER_ID --output-dir /path/to/save`
- Choose output path:
  - `python download_drive_video.py --url "..." --output /path/to/video.mp4`
- Overwrite existing file:
- `python download_drive_video.py --url "..." --output video.mp4 --force`
- Transcribe after download (saves .txt next to video):
  - `python download_drive_video.py --url "..." --transcribe`
- Choose Whisper model and transcript path:
  - `python download_drive_video.py --url "..." --transcribe --whisper-model small --transcript-output out.txt`
  - In folder mode, transcripts save next to each video (one .txt per file).
 - In folder mode, use `--output-dir` to pick the download directory (default: current working directory).

SRT subtitles
- Write SRT along with transcripts:
  - Single file: `python download_drive_video.py --url "..." --srt`
  - With explicit path: `python download_drive_video.py --url "..." --srt --srt-output subtitle.srt`
  - Folder mode: `python download_drive_video.py --folder-url "..." --output-dir ./downloads --srt`
- Behavior:
  - Uses Whisper result segments to create proper SRT with timestamps.
  - In folder mode, `.srt` files save next to each video (one per file). `--srt-output` is ignored in folder mode.
  - Skip optimization: if an `.srt` already exists next to the target video name and its header comments match the Drive file metadata ("Owner" and "Modified"), the tool skips both download and transcription. Header format:
    - `# Owner: <Drive owner displayName>`
    - `# Modified: <Drive modifiedTime>`

On first run it opens a browser window for you to log in and grant read access to Drive. The token is saved to `token.json` for reuse. To store files elsewhere, configure:
- `GOOGLE_OAUTH_CLIENT_SECRETS` to point to your client secrets JSON
- `GOOGLE_OAUTH_TOKEN` to set the token file path

**Notes**
- The script requests scope: `https://www.googleapis.com/auth/drive.readonly`.
- You must have access to the target file; shared drives are supported.
- If the file isn’t a video MIME type, a warning is printed but download proceeds.
- To fetch the original Drive filename automatically, omit `--output`.
 - Whisper uses `ffmpeg` to read media; ensure `ffmpeg` is installed and on PATH.
 - Whisper relies on PyTorch. If `pip install -r requirements.txt` does not install a working Torch for your platform/CUDA, follow https://pytorch.org/get-started/ to install the appropriate `torch` build, then reinstall `openai-whisper` if needed.

**Troubleshooting**
- Invalid credentials: Delete `token.json` and run again to re-authenticate.
- Permission denied: Ensure your Google account can access the file and the owner hasn’t restricted downloads.
- App not verified: In development, you may see an "unverified app" screen unless you publish/verify the OAuth consent.
 - Transcription fails with ffmpeg not found: Install ffmpeg (e.g., macOS: `brew install ffmpeg`, Ubuntu: `sudo apt-get install ffmpeg`).
- Transcription fails due to Torch/whisper: Ensure a compatible PyTorch is installed for your Python and hardware.

**Security**
- Do not commit `credentials.json` or `token.json` to source control.

**Development: Linting & Formatting**
- Install dev tools: `pip install -r dev-requirements.txt`
- Lint with Flake8: `make lint` (or `flake8 src download_drive_video.py`)
- Auto-format with autopep8 in-place: `make format`
- Preview formatting changes (diff only): `make format-check`
