# requirements.txt:
# fastapi==0.111.0
# uvicorn==0.30.1
# selenium==4.22.0
# webdriver-manager==4.0.1 (still useful for local dev, but not strictly needed if path is manual)
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
# from webdriver_manager.chrome import ChromeDriverManager # Commented out for manual path

# --- Configuration ---
# You would ideally load this from environment variables (e.g., using python-dotenv)
# For this example, it's hardcoded.
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
    """
    Verifies the provided authentication token.
    In a real application, this would involve a more robust authentication mechanism
    like JWT validation, database lookup, etc.
    """
    if token != API_AUTH_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token

# --- WebDriver Initialization and Teardown ---
@app.on_event("startup")
async def startup_event():
    """
    Initializes the Selenium WebDriver when the FastAPI application starts up.
    This ensures the browser is ready before handling requests.
    """
    global driver
    print("Initializing Chrome WebDriver...")
    try:
        chrome_options = Options()
        # Run Chrome in headless mode (no visible browser UI)
        chrome_options.add_argument("--headless")
        # Disable GPU hardware acceleration (often needed in headless environments)
        chrome_options.add_argument("--disable-gpu")
        # Disable shared memory usage (important for Docker/container environments)
        chrome_options.add_argument("--no-sandbox")
        # Disable /dev/shm usage (can cause issues in some environments)
        chrome_options.add_argument("--disable-dev-shm-usage")
        # Set a larger window size to ensure elements are rendered correctly
        chrome_options.add_argument("--window-size=1920,1080")
        # Suppress logging to keep console clean
        chrome_options.add_argument("--log-level=3")

        # Specify the path to a manually installed chromedriver binary.
        service = Service(executable_path="/usr/local/bin/chromedriver")

        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("Chrome WebDriver initialized successfully.")
    except Exception as e:
        print(f"Failed to initialize Chrome WebDriver: {e}")
        driver = None # Ensure driver is None if initialization fails

@app.on_event("shutdown")
async def shutdown_event():
    """
    Quits the Selenium WebDriver when the FastAPI application shuts down.
    This releases browser resources.
    """
    global driver
    if driver:
        print("Quitting Chrome WebDriver...")
        driver.quit()
        driver = None
        print("Chrome WebDriver shut down.")

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
    token: str = Depends(verify_token) # Token authentication dependency
):
    """
    Scrapes totalcarcheck.co.uk for the vehicle image URL based on VRM.

    Args:
        vrm (str): The Vehicle Registration Mark (e.g., 'AB12CDE').
        token (str): Authentication token.

    Returns:
        dict: A dictionary containing the 'image_url' or an error message.
    """
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scraping service is not available. WebDriver failed to initialize."
        )

    target_url = f"{TOTAL_CAR_CHECK_BASE_URL}{vrm}"
    image_url = None

    try:
        print(f"Navigating to {target_url} for VRM: {vrm}")
        driver.get(target_url)

        # --- DEBUGGING ADDITIONS START ---
        screenshot_path = f"/tmp/{vrm}_screenshot.png"
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
        # You can retrieve this file from your EC2 instance using scp or similar.

        page_source = driver.page_source
        # print(f"Page source for {vrm}:\n{page_source[:2000]}...") # Print first 2000 chars
        # Consider saving full page source to a file if it's too large for console
        with open(f"/tmp/{vrm}_page_source.html", "w", encoding="utf-8") as f:
            f.write(page_source)
        print(f"Page source saved to: /tmp/{vrm}_page_source.html")
        # --- DEBUGGING ADDITIONS END ---


        # Wait for the image element to be present and visible
        # The ID is 'vehicleImage' as specified by the user.
        # Increased timeout to 30 seconds for debugging purposes
        wait = WebDriverWait(driver, 30) # Increased wait time
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
            detail=f"Scraping timed out. Could not find vehicle image for VRM: {vrm}. The page might not have loaded correctly or the element ID changed. Check logs for screenshot and page source."
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
