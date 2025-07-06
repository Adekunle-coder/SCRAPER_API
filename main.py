import os
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import APIKeyQuery
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

app = FastAPI(
    title="Vehicle Image Scraper API",
    description="API to scrape vehicle images from totalcarcheck.co.uk using VRM and a token.",
    version="1.0.0"
)

# --- Configuration ---
API_AUTH_TOKEN = "91f3846e5d7a474f8d36cfc16f17b1d3e5e5ef4bd2c7a21e3a4d05aa0b36b9d1"
TOTAL_CAR_CHECK_BASE_URL = "https://totalcarcheck.co.uk/FreeCheck?regno="

# --- Token Authentication Dependency ---
api_key_query = APIKeyQuery(name="token", auto_error=False)

def verify_token(token: str = Depends(api_key_query)):
    if token != API_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# --- Health Check ---
@app.get("/")
async def read_root():
    return {"message": "Vehicle Image Scraper API is running."}

# --- Scraper Endpoint ---
@app.get("/scrape_image")
async def scrape_vehicle_image(
    vrm: str,
    token: str = Depends(verify_token)
):
    image_url = None
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        service = Service(executable_path="/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        target_url = f"{TOTAL_CAR_CHECK_BASE_URL}{vrm}"
        driver.get(target_url)

        wait = WebDriverWait(driver, 25)
        image_element = wait.until(
            EC.presence_of_element_located((By.ID, "vehicleImage"))
        )

        image_url = image_element.get_attribute("src")
        print(f"[INFO] Found image URL: {image_url} for VRM: {vrm}")

        if image_url:
            return {"image_url": image_url}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image found but 'src' was empty for VRM: {vrm}"
            )

    except TimeoutException:
        print(f"[ERROR] Timeout: 'vehicleImage' not found for VRM: {vrm}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Scraping timed out. Could not find vehicle image."
        )

    except WebDriverException as e:
        print(f"[ERROR] WebDriver error for VRM {vrm}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"WebDriver error occurred: {e}"
        )

    except Exception as e:
        print(f"[ERROR] Unexpected error for VRM {vrm}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

    finally:
        if driver:
            driver.quit()
