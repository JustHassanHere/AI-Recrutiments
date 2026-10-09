from googleapiclient.discovery import build
from gmail_auth import get_credentials

def get_gmail_service():
    credentials = get_credentials()
    service = build('gmail', 'v1', credentials=credentials)
    return service