import os
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"
CREDENTIALS_FILE = "credentials.json"


def save_token(credentials):
    with open(TOKEN_FILE, "w") as token:
        token.write(credentials.to_json())


def login():
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
    credentials = flow.run_local_server(port=0)
    save_token(credentials)
    return credentials


def get_credentials():
    credentials = None

    if os.path.exists(TOKEN_FILE):
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # token is still valid
    if credentials and credentials.valid:
        return credentials

    # token expired: try to refresh it
    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            save_token(credentials)
            return credentials
        except RefreshError:
            print("Token expired or revoked. Please log in again.")

    # no token, or refresh failed: log in again
    return login()