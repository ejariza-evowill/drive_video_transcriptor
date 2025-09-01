from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


import os
from typing import Sequence
from typing import Optional

DEFAULT_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def get_credentials(
    client_secrets_path: str,
    token_path: str = "token.json",
    scopes: Optional[Sequence[str]] = None,
) -> Credentials:
    """Load or create OAuth user credentials for Google APIs.

    - Uses an installed app flow and stores the token in `token_path`.
    - Defaults to Drive read-only scope unless `scopes` is provided.
    """
    scopes = list(scopes or DEFAULT_SCOPES)
    creds: Optional[Credentials] = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_path, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_path, "w") as token:
            token.write(creds.to_json())
    return creds
