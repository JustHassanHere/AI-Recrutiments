import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.title("CV Screening")

try:
    jobs = requests.get(f"{API_URL}/jobs").json()
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to the API. Is Uvicorn running?")
    st.stop()

if not jobs:
    st.info("Create a job first.")
    st.stop()

job_ids = [job["id"] for job in jobs]
job_names = {job["id"]: f"{job['id']} - {job['title']}" for job in jobs}

selected_id = st.selectbox("Job", job_ids, index=len(job_ids) - 1, format_func=lambda i: job_names[i])
job = [j for j in jobs if j["id"] == selected_id][0]

st.write("**Must-Have requirements:**", ", ".join(job["must_have"]) if job["must_have"] else "None selected")

if st.button("Start CV screening"):
    with st.spinner("Reading CVs from Gmail and matching them... this can take a few minutes"):
        try:
            response = requests.post(f"{API_URL}/jobs/{selected_id}/screen", timeout=900)
            if response.status_code == 200:
                stats = response.json()
                st.success("Screening finished.")
                col1, col2, col3 = st.columns(3)
                col1.metric("New CVs", stats["new"])
                col2.metric("Already processed", stats["skipped"])
                col3.metric("Errors", stats["errors"])
            else:
                st.error(response.json().get("detail", "Something went wrong"))
        except requests.exceptions.ConnectionError:
            st.error("Cannot connect to the API. Is Uvicorn running?")