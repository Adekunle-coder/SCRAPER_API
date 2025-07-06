from fastapi import FastAPI, HTTPException, status
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# --- App Initialization ---
app = FastAPI(
    title="Vehicle Image Scraper API",
    description="API to scrape vehicle images from totalcarcheck.co.uk using VRM and a token.",
    version="1.0.0"
)

# --- Configuration ---
API_AUTH_TOKEN = "91f3846e5d7a474f8d36cfc16f17b1d3e5e5ef4bd2c7a21e3a4d05aa0b36b9d1"
TOTAL_CAR_CHECK_BASE_URL = "https://totalcarcheck.co.uk/FreeCheck?regno="
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"

# --- Utilities ---
def get_chrome_driver() -> webdriver.Chrome:
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # updated headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--remote-debugging-port=9222")  # optional but useful
    chrome_options.add_argument("--window-size=1920,1080")
    
    service = Service(executable_path="/usr/local/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)

# --- Health Check ---
@app.get("/")
def health_check():
    return {"message": "Vehicle Image Scraper API is running."}

# --- Scrape Vehicle Image ---
@app.get("/scrape_image")
def scrape_vehicle_image(vrm: str, token: str):
    if token != API_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    driver = None
    try:
        driver = get_chrome_driver()
        driver.get(f"{TOTAL_CAR_CHECK_BASE_URL}{vrm}")

        image = driver.find_element(By.ID, "vehicleImage")
        if image:
            img_url = image.get_attribute("src")
            return img_url
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image found but 'src' was empty for VRM: {vrm}"
            )
       
    except TimeoutException:
        print(f"[ERROR] Timeout: Image not found for VRM {vrm}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Scraping timed out. Could not find vehicle image."
        )

    except WebDriverException as e:
        print(f"[ERROR] WebDriver error for VRM {vrm}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Selenium WebDriver error: {e}"
        )

    except Exception as e:
        print(f"[ERROR] Unexpected error for VRM {vrm}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error occurred: {e}"
        )

    finally:
        if driver:
            driver.quit()
