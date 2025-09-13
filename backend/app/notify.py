import requests
from app.config import ONESIGNAL_APP_ID, ONESIGNAL_API_KEY
def send_one_signal(external_ids: list, message: str, data: dict = None):
    payload = {"app_id": ONESIGNAL_APP_ID, "include_external_user_ids": external_ids, "contents": {"en": message}}
    if data:
        payload["data"] = data
    headers = {"Authorization": f"Basic {ONESIGNAL_API_KEY}", "Content-Type": "application/json"}
    requests.post("https://onesignal.com/api/v1/notifications", json=payload, headers=headers)
