import io, mimetypes
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from app.config import GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, GOOGLE_OAUTH_REDIRECT_URI, GOOGLE_SERVICE_ACCOUNT_JSON
def flow_for_user(state: str):
    flow = Flow.from_client_config({
        "web": {
            "client_id": GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": GOOGLE_OAUTH_CLIENT_SECRET,
            "redirect_uris": [GOOGLE_OAUTH_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }, scope=["https://www.googleapis.com/auth/drive.file"], state=state)
    flow.redirect_uri = GOOGLE_OAUTH_REDIRECT_URI
    return flow
def build_drive_service(creds):
    service = build('drive', 'v3', credentials=creds)
    return service
def upload_bytes_to_drive(service, filename: str, data: bytes, mimetype: str = None):
    media = MediaIoBaseUpload(io.BytesIO(data), mimetype=mimetype or 'application/octet-stream', resumable=True)
    file_metadata = {"name": filename}
    f = service.files().create(body=file_metadata, media_body=media, fields="id,name,mimeType,size,webViewLink").execute()
    return f
def list_files_in_drive(service, page_size: int = 100):
    r = service.files().list(pageSize=page_size, fields="files(id,name,mimeType,size,webViewLink)").execute()
    return r.get("files", [])
