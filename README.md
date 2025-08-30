**Google Drive Video Downloader**
- Purpose: Download a Google Drive video using your own account via OAuth login.

**Features**
- OAuth 2.0 user login (Installed app flow).
- Downloads with your permissions (no service account).
- Accepts a Drive file ID or full URL.
- Saves and reuses token in `token.json`.

**Prerequisites**
- Python 3.9+
- A Google Cloud project with Drive API enabled.
- An OAuth 2.0 Client ID for Desktop app.

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
- Choose output path:
  - `python download_drive_video.py --url "..." --output /path/to/video.mp4`
- Overwrite existing file:
  - `python download_drive_video.py --url "..." --output video.mp4 --force`

On first run it opens a browser window for you to log in and grant read access to Drive. The token is saved to `token.json` for reuse. To store files elsewhere, configure:
- `GOOGLE_OAUTH_CLIENT_SECRETS` to point to your client secrets JSON
- `GOOGLE_OAUTH_TOKEN` to set the token file path

**Notes**
- The script requests scope: `https://www.googleapis.com/auth/drive.readonly`.
- You must have access to the target file; shared drives are supported.
- If the file isn’t a video MIME type, a warning is printed but download proceeds.
- To fetch the original Drive filename automatically, omit `--output`.

**Troubleshooting**
- Invalid credentials: Delete `token.json` and run again to re-authenticate.
- Permission denied: Ensure your Google account can access the file and the owner hasn’t restricted downloads.
- App not verified: In development, you may see an "unverified app" screen unless you publish/verify the OAuth consent.

**Security**
- Do not commit `credentials.json` or `token.json` to source control.

