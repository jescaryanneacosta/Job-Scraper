import streamlit as st
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd
import matplotlib.pyplot as plt
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import requests  # <-- you forgot this!

# Set up global driver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# Load keywords
def load_keywords(json_file):
    data = json.load(json_file)
    keywords = []
    for items in data.values():
        keywords.extend(items)
    return [kw.lower() for kw in keywords]

# Indeed scraper with Selenium
def scrape_indeed(query, location, pages=3):
    descriptions = []
    base_url = "https://ph.indeed.com/jobs"

    for page in range(pages):
        start = page * 10
        search_url = f"{base_url}?q={query}&l={location}&start={start}"
        driver.get(search_url)
        time.sleep(2)

        job_cards = driver.find_elements(By.CLASS_NAME, "jcs-JobTitle")
        print(f"Indeed Page {page+1}: Found {len(job_cards)} job links")

        job_links = [card.get_attribute("href") for card in job_cards if card.get_attribute("href")]

        for link in job_links:
            try:
                driver.get(link)
                time.sleep(2)
                desc_div = driver.find_element(By.ID, "jobDescriptionText")
                descriptions.append(desc_div.text)
            except Exception as e:
                print("Error fetching job desc:", e)
                continue

    return descriptions

# JobStreet scraper
def scrape_jobstreet(query, pages=2):
    descriptions = []
    base_url = f"https://www.jobstreet.com.ph/en/job-search/{query.replace(' ', '-')}-jobs/"

    for page in range(1, pages + 1):
        full_url = f"{base_url}?page={page}"
        driver.get(full_url)
        time.sleep(3)

        jobs = driver.find_elements(By.CSS_SELECTOR, 'a[data-automation="jobTitle"]')
        print(f"JobStreet Page {page}: Found {len(jobs)} job links")

        links = [job.get_attribute("href") for job in jobs if job.get_attribute("href")]

        for link in links:
            try:
                driver.get(link)
                time.sleep(2)
                job_desc_el = driver.find_element(By.CLASS_NAME, "sx2jih0")
                descriptions.append(job_desc_el.text)
            except Exception as e:
                print("Error loading job description:", e)
                continue

    return descriptions

# Count keyword mentions
def count_keywords(descriptions, keywords):
    counter = Counter()
    for desc in descriptions:
        text = desc.lower()
        for keyword in keywords:
            if keyword in text:
                counter[keyword] += 1
    return counter

# Streamlit UI
st.title("Frontend Job Tech Trends 📈")

query = st.text_input("Job title (e.g., frontend developer)", value="frontend developer")
location = st.text_input("Location (for Indeed)", value="Philippines")
pages = st.slider("Pages to scrape per site", 1, 5, 2)
uploaded_file = st.file_uploader("Upload JSON file with frontend technologies", type="json")

if st.button("Run Scraper") and uploaded_file:
    with st.spinner("Scraping job listings..."):
        keywords = load_keywords(uploaded_file)
        indeed_desc = scrape_indeed(query, location, pages)
        jobstreet_desc = scrape_jobstreet(query, pages)
        all_desc = indeed_desc + jobstreet_desc

        print(f"Total descriptions scraped: {len(all_desc)}")
        counts = count_keywords(all_desc, keywords)

        if counts:
            df = pd.DataFrame(counts.items(), columns=["Technology", "Frequency"])
            df = df.sort_values("Frequency", ascending=False)

            st.subheader("📊 Frequency of Technologies")
            st.bar_chart(df.set_index("Technology"))

            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False).encode('utf-8'),
                file_name="frontend_tech_trends.csv",
                mime="text/csv"
            )
        else:
            st.warning("No technologies were found in the scraped job listings.")

driver.quit()
