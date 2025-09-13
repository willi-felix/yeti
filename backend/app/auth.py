import firebase_admin
from firebase_admin import credentials, auth
from app.config import FIREBASE_CRED_JSON
from dotenv import load_dotenv
load_dotenv()
if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_JSON)
    firebase_admin.initialize_app(cred)
def verify_id_token(token: str):
    decoded = auth.verify_id_token(token)
    return decoded
