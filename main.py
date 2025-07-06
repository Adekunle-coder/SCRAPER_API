from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup


app = FastAPI()

# Save as an env variable but this would work for now.
API_TOKEN = "91f3846e5d7a474f8d36cfc16f17b1d3e5e5ef4bd2c7a21e3a4d05aa0b36b9d1"

referer = "https://totalcarcheck.co.uk/"
accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
accept_language = "en-GB,en;q=0.6"
cookie = "zero-chakra-ui-color-mode=light-zero; AMP_MKTG_8f1ede8e9c=JTdCJTIycmVmZXJyZXIlMjIlM0ElMjJodHRwcyUzQSUyRiUyRnd3dy5nb29nbGUuY29tJTJGJTIyJTJDJTIycmVmZXJyaW5nX2RvbWFpbiUyMiUzQSUyMnd3dy5nb29nbGUuY29tJTIyJTdE; AMP_8f1ede8e9c=JTdCJTIyZGV2aWNlSWQlMjIlM0ElMjI1MjgxOGYyNC05ZGQ3LTQ5OTAtYjcxMC01NTY0NzliMzAwZmYlMjIlMkMlMjJzZXNzaW9uSWQlMjIlM0ExNzA4MzgxNTQ4ODQzJTJDJTIyb3B0T3V0JTIyJTNBZmFsc2UlMkMlMjJsYXN0RXZlbnRUaW1lJTIyJTNBMTcwODM4MjE1NTQ2MCUyQyUyMmxhc3RFdmVudElkJTIyJTNBNiU3RA=="
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

custom_headers = {
    "User-Agent": user_agent,
    "Accept": accept,
    "Accept-Language": accept_language,
    "Cookie": cookie,
    "Referer": referer
}

@app.get("/get-vehicle-image")
def get_vehicle_image(vrm: str, token: str = Query(...)):
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        url = f"https://totalcarcheck.co.uk/FreeCheck?regno={vrm}"
        response = requests.get(url, headers=custom_headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        img = soup.find("img", {"id": "vehicleImage"})
        if img and img.get("src"):
            return {"image_url": img["src"]}
        else:
            return {"image_url": None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
