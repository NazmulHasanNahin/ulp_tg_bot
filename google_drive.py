import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# 🔐 Google Drive authentication scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']


# 📤 Upload file and return file_id
def upload_file_to_drive(file_path):
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)

    file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)

    print(f"🔄 Uploading {file_name} to Google Drive...")

    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    file_id = file.get('id')

    # Make the file public
    service.permissions().create(
        fileId=file_id,
        body={'type': 'anyone', 'role': 'reader'}
    ).execute()

    print(f"✅ Upload complete. File ID: {file_id}")
    return file_id


# 🌐 Create a shareable public link
def create_shareable_link(file_id):
    return f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"


# 🔑 Helper: Load or generate credentials
def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
