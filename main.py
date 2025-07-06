import undetected_chromedriver as uc
from fastapi import FastAPI, HTTPException, status
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

# --- Utilities ---
def get_undetected_driver() -> uc.Chrome:
    options = uc.ChromeOptions()
    options.add_argument("--headless")  
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)

    return uc.Chrome(options=options, headless=True)

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
        driver = get_undetected_driver()
        driver.get(f"{TOTAL_CAR_CHECK_BASE_URL}{vrm}")

        wait = WebDriverWait(driver, 20)
        image_element = wait.until(
            EC.presence_of_element_located((By.ID, "vehicleImage"))
        )

        image_url = image_element.get_attribute("src")
        if image_url:
            return {"image_url": image_url}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image found but 'src' was empty for VRM: {vrm}"
            )

    except TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Scraping timed out. 'vehicleImage' not found for VRM: {vrm}"
        )

    except WebDriverException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Selenium WebDriver error: {e}"
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error occurred: {e}"
        )

    finally:
        if driver:
            driver.quit()
