import streamlit as st
from bs4 import BeautifulSoup
from collections import Counter
import pandas as pd
import requests
import json
import time

# ---------- Load JSON Keywords ----------
def load_keywords(json_file):
    data = json.load(json_file)
    keywords = []
    for items in data.values():
        keywords.extend(items)
    return [kw.lower() for kw in keywords]

# ---------- Indeed Scraper ----------
def scrape_indeed_bs(query, location, pages=3):
    base_url = "https://ph.indeed.com/jobs"
    headers = {"User-Agent": "Mozilla/5.0"}
    descriptions = []

    for page in range(pages):
        params = {
            "q": query,
            "l": location,
            "start": page * 10
        }
        response = requests.get(base_url, headers=headers, params=params)
        soup = BeautifulSoup(response.text, "html.parser")

        job_cards = soup.select("a.jcs-JobTitle")
        print(f"Indeed Page {page + 1}: Found {len(job_cards)} job cards")

        for job_card in job_cards:
            href = job_card.get("href")
            if href:
                job_url = "https://ph.indeed.com" + href
                try:
                    job_page = requests.get(job_url, headers=headers)
                    job_soup = BeautifulSoup(job_page.text, "html.parser")
                    desc = job_soup.find("div", id="jobDescriptionText")
                    if desc:
                        descriptions.append(desc.get_text(separator=" ", strip=True))
                        time.sleep(0.5)
                except Exception as e:
                    print("Error fetching Indeed job description:", e)

    return descriptions

# ---------- JobStreet Scraper ----------
def scrape_jobstreet_bs(query, pages=3):
    base_url = "https://www.jobstreet.com.ph/en/job-search/"
    headers = {"User-Agent": "Mozilla/5.0"}
    descriptions = []

    for page in range(1, pages + 1):
        url = f"{base_url}{query.replace(' ', '-')}-jobs/?page={page}"
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        job_cards = soup.select('a[data-automation="jobTitle"]')
        print(f"JobStreet Page {page}: Found {len(job_cards)} job cards")

        for job_card in job_cards:
            href = job_card.get("href")
            if href and href.startswith("/job/"):
                job_url = "https://www.jobstreet.com.ph" + href
                try:
                    job_page = requests.get(job_url, headers=headers)
                    job_soup = BeautifulSoup(job_page.text, "html.parser")
                    desc = job_soup.find("div", class_="sx2jih0")
                    if desc:
                        descriptions.append(desc.get_text(separator=" ", strip=True))
                        time.sleep(0.5)
                except Exception as e:
                    print("Error fetching JobStreet job description:", e)

    return descriptions

# ---------- Keyword Counter ----------
def count_keywords(descriptions, keywords):
    counter = Counter()
    for desc in descriptions:
        text = desc.lower()
        for keyword in keywords:
            if keyword in text:
                counter[keyword] += 1
    return counter

# ---------- Streamlit UI ----------
st.title("Frontend Job Tech Trends 📈")

query = st.text_input("Job title (e.g., frontend developer)", value="frontend developer")
location = st.text_input("Location (for Indeed)", value="Philippines")
pages = st.slider("Pages to scrape per site", 1, 5, 2)
uploaded_file = st.file_uploader("Upload JSON file with frontend technologies", type="json")

if st.button("Run Scraper") and uploaded_file:
    with st.spinner("Scraping job listings..."):
        keywords = load_keywords(uploaded_file)

        indeed_desc = scrape_indeed_bs(query, location, pages)
        jobstreet_desc = scrape_jobstreet_bs(query, pages)

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
