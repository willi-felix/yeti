import requests
from app.config import GIPHY_API_KEY
def search_gif(q: str, limit: int = 1):
    r = requests.get("https://api.giphy.com/v1/gifs/search", params={"api_key": GIPHY_API_KEY, "q": q, "limit": limit})
    if r.status_code == 200:
        d = r.json()
        if d.get("data"):
            gif = d["data"][0]
            return {"id": gif["id"], "url": gif["images"]["downsized_medium"]["url"], "title": gif.get("title"), "embed":"Powered by Giphy"}
    return None
