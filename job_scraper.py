import requests
import json
from collections import Counter
import streamlit as st
import pandas as pd
import re
from collections import Counter

# ---------- Load JSON Keywords ----------
def load_keywords(json_file):
    data = json.load(json_file)
    keywords = []
    for items in data.values():
        keywords.extend(items)
    return [kw.lower() for kw in keywords]

# ---------- Fetch Jobs from Remotive API (with fallback) ----------
def fetch_jobs_remotive(query, limit=50):
    url = "https://remotive.com/api/remote-jobs"
    params = {"search": query, "limit": limit}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
        return [
            (job.get("title", "") + " " + job.get("description", "")).lower()
            for job in jobs
        ]
    except requests.exceptions.HTTPError as e:
        st.warning(f"🔀 Remotive API error ({e}). Falling back to RemoteOK…")
        return fetch_jobs_remoteok(limit)
    except requests.exceptions.RequestException as e:
        st.warning(f"🔀 Error fetching Remotive ({e}). Falling back to RemoteOK…")
        return fetch_jobs_remoteok(limit)

# ---------- Fetch Jobs from RemoteOK API ----------
def fetch_jobs_remoteok(limit=50):
    url = "https://remoteok.com/api"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()[1:]  # skip first metadata element
        jobs = data[:limit]     # take top N postings
        return [
            (job.get("position", "") + " " + job.get("description", "")).lower()
            for job in jobs
        ]
    except Exception as e:
        st.error(f"❌ RemoteOK fallback failed: {e}")
        return []

# ---------- Count Keywords in Descriptions ----------
def count_keywords(descriptions, keywords):
    counter = Counter()
    # pre‑compile one regex per keyword
    patterns = {
        kw: re.compile(r"\b" + re.escape(kw) + r"\b")
        for kw in keywords
    }
    for desc in descriptions:
        text = desc.lower()
        for kw, pat in patterns.items():
            if pat.search(text):
                counter[kw] += 1
    return counter


# ---------- Streamlit UI ----------
st.title("Frontend Job Tech Trends 📈 (Remotive + RemoteOK)")

query = st.text_input("Job title (e.g., frontend developer)", "frontend developer")
uploaded_file = st.file_uploader("Upload JSON file with frontend technologies", type="json")
limit = st.slider("Max job listings to fetch", 10, 500, 100, step=50)

if st.button("Run Analysis") and uploaded_file:
    with st.spinner("Fetching job listings…"):
        keywords = load_keywords(uploaded_file)

        descriptions = fetch_jobs_remotive(query, limit=limit)
        st.write(f"🔎 Fetched {len(descriptions)} job listings")

        if not descriptions:
            st.error("No job listings returned. Try changing your query or increasing the limit.")
        else:
            counts = count_keywords(descriptions, keywords)
            if counts:
                # Build and sort DataFrame
                df = pd.DataFrame(counts.items(), columns=["Technology", "Frequency"])
                df = df.sort_values("Frequency", ascending=False)
                df["Technology"] = pd.Categorical(
                    df["Technology"],
                    categories=df["Technology"],
                    ordered=True
                )

                st.subheader("📊 Technology Frequencies (most → least)")
                st.bar_chart(df.set_index("Technology"))

                st.download_button(
                    "Download CSV",
                    data=df.to_csv(index=False).encode("utf-8"),
                    file_name="frontend_tech_trends.csv",
                    mime="text/csv"
                )
            else:
                st.warning("None of your keywords were found in the job listings.")
