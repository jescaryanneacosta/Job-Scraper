import requests
import json
from collections import Counter
import http.client
import streamlit as st
import pandas as pd

# ---------- Load JSON Keywords ----------
def load_keywords(json_file):
    data = json.load(json_file)
    keywords = []
    for items in data.values():
        keywords.extend(items)
    return [kw.lower() for kw in keywords]

# ---------- Fetch Jobs Using JSearch API ----------
def fetch_jobs(query, api_key, num_results=10):
    url = "https://jsearch.p.rapidapi.com/search"
    
    headers = {
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        "X-RapidAPI-Key": api_key
    }
    
    params = {
        "query": query,
        "page": "1",  # You can loop over pages later if needed
        "num_pages": "1",  # Change this for more results
        "page_size": str(num_results)
    }

    response = requests.get(url, headers=headers, params=params)
    job_data = response.json()
    job_descriptions = []

    if "jobs" in job_data:
        for job in job_data["jobs"]:
            title = job.get("job_title", "").lower()
            description = job.get("job_description", "").lower()
            job_descriptions.append(f"{title} {description}")
    
    return job_descriptions

# ---------- Fetch Estimated Salary Using JSearch API ----------
def fetch_salary_estimate(api_key, location="ANY", years_of_experience="ALL"):
    conn = http.client.HTTPSConnection("jsearch.p.rapidapi.com")
    headers = {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": "jsearch.p.rapidapi.com"
    }
    
    # You can pass more parameters to customize the salary estimate
    conn.request("GET", f"/estimated-salary?location_type={location}&years_of_experience={years_of_experience}", headers=headers)

    res = conn.getresponse()
    data = res.read()
    salary_data = json.loads(data.decode("utf-8"))

    if "estimated_salary" in salary_data:
        return salary_data["estimated_salary"]
    else:
        return None

# ---------- Count Keywords in Descriptions ----------
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
uploaded_file = st.file_uploader("Upload JSON file with frontend technologies", type="json")
api_key = st.text_input("Enter your X-RapidAPI-Key", value="", type="password")

if st.button("Run Scraper") and uploaded_file and api_key:
    with st.spinner("Fetching job listings..."):
        keywords = load_keywords(uploaded_file)
        descriptions = fetch_jobs(query, api_key, num_results=50)
        
        counts = count_keywords(descriptions, keywords)

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
            st.warning("No job listings found or no technologies matched.")
        
        # Fetch and display the salary estimate
        st.subheader("💰 Estimated Salary")
        salary = fetch_salary_estimate(api_key)
        if salary:
            st.write(f"Estimated Salary: ${salary['min']} - ${salary['max']} per year")
        else:
            st.write("Could not fetch salary estimate.")
