
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
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            try:
                page = browser.new_page()
                page.goto(f"https://totalcarcheck.co.uk/FreeCheck?regno={vrm}", timeout=15000)
                page.wait_for_selector("#vehicleImage", timeout=10000)
                img_src = page.locator("#vehicleImage").get_attribute("src")
                if not img_src:
                    raise HTTPException(status_code=404, detail="Image not found")
                return {"image_url": img_src}
            finally:
                browser.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
