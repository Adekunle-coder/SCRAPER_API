# from fastapi import FastAPI, HTTPException, Query
# from pydantic import BaseModel
# import requests
# from bs4 import BeautifulSoup
# import traceback  # for full stack trace logging

# app = FastAPI()

# # TODO: Store securely via os.getenv in production
# API_TOKEN = "91f3846e5d7a474f8d36cfc16f17b1d3e5e5ef4bd2c7a21e3a4d05aa0b36b9d1"

# # Headers to mimic a browser
# referer = "https://totalcarcheck.co.uk/"
# accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
# accept_language = "en-GB,en;q=0.6"
# cookie = "zero-chakra-ui-color-mode=light-zero; AMP_MKTG_8f1ede8e9c=... (shortened for readability)"
# user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# custom_headers = {
#     "User-Agent": user_agent,
#     "Accept": accept,
#     "Accept-Language": accept_language,
#     "Cookie": cookie,
#     "Referer": referer
# }

# @app.get("/get-vehicle-image")
# def get_vehicle_image(vrm: str, token: str = Query(...)):
#     if token != API_TOKEN:
#         raise HTTPException(status_code=403, detail="Invalid token")

#     try:
#         url = f"https://totalcarcheck.co.uk/FreeCheck?regno={vrm}"
#         response = requests.get(url, headers=custom_headers)
#         response.raise_for_status()

#         soup = BeautifulSoup(response.text, "html.parser")
#         img = soup.find("img", {"id": "vehicleImage"})

#         if img and img.get("src"):
#             return {"image_url": img["src"]}
#         else:
#             return {"image_url": None, "message": "Vehicle image not found on the page"}

#     except Exception as e:
#         print("❌ An error occurred while fetching the image:")
#         traceback.print_exc()  # full traceback in Render logs
#         raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")



# Install playwright with: pip install playwright && playwright install
from fastapi import FastAPI, HTTPException
from playwright.sync_api import sync_playwright

app = FastAPI()
API_TOKEN = "91f3846e5d7a474f8d36cfc16f17b1d3e5e5ef4bd2c7a21e3a4d05aa0b36b9d1"

@app.get("/get-vehicle-image")
def get_vehicle_image(vrm: str, token: str):
    if token != API_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"https://totalcarcheck.co.uk/FreeCheck?regno={vrm}")
            img_src = page.locator("#vehicleImage").get_attribute("src")
            browser.close()
            return {"image_url": img_src}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
