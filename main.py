# requirements.txt:
# fastapi==0.111.0
# uvicorn==0.30.1
# selenium==4.22.0
# webdriver-manager==4.0.1
# python-dotenv==1.0.1 (optional, for environment variables)

import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

# For local development, webdriver_manager can automatically download ChromeDriver.
# For production deployment, it's recommended to install ChromeDriver manually
# and specify its path directly, as automatic downloads might not be reliable
# in containerized or serverless environments.
from webdriver_manager.chrome import ChromeDriverManager


API_AUTH_TOKEN = "91f3846e5d7a474f8d36cfc16f17b1d3e5e5ef4bd2c7a21e3a4d05aa0b36b9d1"
TOTAL_CAR_CHECK_BASE_URL = "https://totalcarcheck.co.uk/FreeCheck?regno="

# Global WebDriver instance (for simplicity in this example).
# IMPORTANT: In a production API, creating a new WebDriver for each request
# is very resource-intensive and slow. A more scalable solution would involve
# a WebDriver pool or a dedicated scraping service.
driver: webdriver.Chrome = None

app = FastAPI(
    title="Vehicle Image Scraper API",
    description="API to scrape vehicle images from totalcarcheck.co.uk using VRM and a token.",
    version="1.0.0"
)

# --- Dependency for Token Authentication ---
def verify_token(token: str):

    if token != API_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# --- API Endpoints ---
@app.get("/")
async def read_root():
    """
    Basic health check endpoint.
    """
    return {"message": "Vehicle Image Scraper API is running."}

@app.get("/scrape_image")
async def scrape_vehicle_image(
    vrm: str,
    token: str, # Token authentication dependency
):
    global driver
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        service = Service(executable_path="/usr/local/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        if not driver:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scraping service is not available. WebDriver failed to initialize."
            )

        target_url = f"{TOTAL_CAR_CHECK_BASE_URL}{vrm}"
        image_url = None

        driver.get(target_url)
        wait = WebDriverWait(driver, 20) # Wait up to 20 seconds
        image_element = wait.until(
            EC.presence_of_element_located((By.ID, "vehicleImage"))
        )

        image_url = image_element.get_attribute("src")
        print(f"Found image URL: {image_url} for VRM: {vrm}")

        if image_url:
            return {"image_url": image_url}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Image URL not found for VRM: {vrm}. Element 'vehicleImage' found but 'src' attribute was empty."
            )

    except TimeoutException:
        print(f"Timeout: 'vehicleImage' element not found within time for VRM: {vrm}")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Scraping timed out. Could not find vehicle image for VRM: {vrm}. The page might not have loaded correctly or the element ID changed."
        )
    except WebDriverException as e:
        print(f"WebDriver error during scraping for VRM: {vrm}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An internal error occurred during scraping for VRM: {vrm}. Please try again later. (Error: {e})"
        )
    except Exception as e:
        print(f"An unexpected error occurred for VRM: {vrm}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {e}"
        )

    except Exception as e:
        print(f"Failed to initialize Chrome WebDriver: {e}")
        driver = None 
    

    
        

# --- How to Run ---
# 1. Save the code above as `main.py`.
# 2. Create a `requirements.txt` file with the listed dependencies.
# 3. Run `pip install -r requirements.txt` in your terminal.
# 4. Set the environment variable: `export API_AUTH_TOKEN="your_secret_token_here"`
#    (On Windows: `set API_AUTH_TOKEN="your_secret_token_here"`)
# 5. Run the application: `uvicorn main:app --host 0.0.0.0 --port 8000`
#
# You can then access the API documentation at http://localhost:8000/docs
#
# Example API Call (replace with your token and VRM):
# GET http://localhost:8000/scrape_image?vrm=AB12CDE&token=your_secret_token_here
