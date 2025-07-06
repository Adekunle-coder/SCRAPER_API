from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup


app = FastAPI()

# Save as an env variable but this would work for now.
API_TOKEN = "91f3846e5d7a474f8d36cfc16f17b1d3e5e5ef4bd2c7a21e3a4d05aa0b36b9d1"

@app.get("/get-vehicle-image")
def get_vehicle_image(vrm: str, token: str = Query(...)):
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        url = f"https://totalcarcheck.co.uk/FreeCheck?regno={vrm}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Referer": "https://totalcarcheck.co.uk/",
        }

        response = requests.get(url, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        img = soup.find("img", {"id": "vehicleImage"})
        if img and img.get("src"):
            return {"image_url": img["src"]}
        else:
            return {"image_url": None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
