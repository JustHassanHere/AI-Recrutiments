import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.title("Create Job")

title = st.text_input("Job title")
description = st.text_area("Job description", height=250)

if st.button("Create job and extract requirements"):
    if not title.strip() or not description.strip():
        st.error("Please enter a title and a job description.")
    else:
        with st.spinner("AI is extracting the requirements..."):
            try:
                response = requests.post(
                    f"{API_URL}/jobs",
                    json={"title": title, "description": description},
                    timeout=120,
                )
                if response.status_code == 200:
                    st.session_state["selected_job_id"] = response.json()["id"]
                    st.success("Job created.")
                else:
                    st.error(response.json().get("detail", "Something went wrong"))
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to the API. Is Uvicorn running?")

st.divider()
st.subheader("Review requirements and choose Must-Have")

try:
    jobs = requests.get(f"{API_URL}/jobs").json()
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to the API. Is Uvicorn running?")
    st.stop()

if not jobs:
    st.info("No jobs yet.")
    st.stop()

job_ids = [job["id"] for job in jobs]
job_names = {job["id"]: f"{job['id']} - {job['title']}" for job in jobs}

default_index = len(job_ids) - 1
if st.session_state.get("selected_job_id") in job_ids:
    default_index = job_ids.index(st.session_state["selected_job_id"])

selected_id = st.selectbox("Job", job_ids, index=default_index, format_func=lambda i: job_names[i])
job = [j for j in jobs if j["id"] == selected_id][0]

if job["requirements"]:
    st.dataframe(pd.DataFrame(job["requirements"]))
else:
    st.warning("The AI did not find any requirements.")

options = list(dict.fromkeys([r["text"] for r in job["requirements"]]))
default = [item for item in job["must_have"] if item in options]

must_have = st.multiselect("Must-Have requirements", options, default=default, key=f"must_{selected_id}")

if st.button("Save Must-Have"):
    response = requests.put(f"{API_URL}/jobs/{selected_id}/must-have", json={"must_have": must_have})
    if response.status_code == 200:
        st.success("Must-Have requirements saved.")
    else:
        st.error(response.json().get("detail", "Something went wrong"))