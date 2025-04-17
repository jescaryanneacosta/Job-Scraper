from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get("https://ph.indeed.com/jobs?q=frontend+developer&l=Philippines")

# Wait for job cards to load (wait up to 10 seconds)
try:
    job_cards = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-testid='jobTitle']"))
    )
    print("Found", len(job_cards), "job cards")

    for job in job_cards[:3]:
        print("-", job.text)

finally:
    driver.quit()
