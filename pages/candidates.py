import streamlit as st
import requests
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.title("Candidates")

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
top_n = st.number_input("Shortlist size (Top N)", min_value=1, value=20)

data = requests.get(f"{API_URL}/jobs/{selected_id}/candidates", params={"top_n": top_n}).json()
stats = data["stats"]
qualified = data["qualified"]
not_qualified = data["not_qualified"]

# statistics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total", stats["total"])
col2.metric("Qualified", stats["qualified"])
col3.metric("Missing Must-Have", stats["not_qualified"])
col4.metric("Shortlisted", stats["shortlist"])


def make_table(candidates):
    rows = []
    for c in candidates:
        rows.append({
            "ID": c["id"],
            "File": c["filename"],
            "From": c["sender"],
            "Score %": c["score"],
            "Decision": c["decision"],
            "Missing Must-Have": ", ".join(c["missing_must"]),
        })
    return pd.DataFrame(rows)


st.subheader("Qualified candidates (ranked)")
if qualified:
    st.dataframe(make_table(qualified))
else:
    st.info("No qualified candidates yet.")

st.subheader("Candidates who miss a Must-Have")
if not_qualified:
    st.dataframe(make_table(not_qualified))
else:
    st.info("None.")

# candidate details
all_candidates = qualified + not_qualified
if not all_candidates:
    st.stop()

st.divider()
st.subheader("Candidate details")

names = {c["id"]: f"{c['id']} - {c['filename']}" for c in all_candidates}
candidate_id = st.selectbox("Choose a candidate", list(names.keys()), format_func=lambda i: names[i])
candidate = [c for c in all_candidates if c["id"] == candidate_id][0]

st.write("**From:**", candidate["sender"])
st.write("**Subject:**", candidate["subject"])
st.write("**Score:**", f"{candidate['score']}%")
st.write("**Current decision:**", candidate["decision"])

if candidate["missing_must"]:
    st.error("Missing Must-Have: " + ", ".join(candidate["missing_must"]))
else:
    st.success("Meets all Must-Have requirements")

st.write("**Matching results and evidence**")
st.dataframe(pd.DataFrame(candidate["results"]))

cv_response = requests.get(f"{API_URL}/candidates/{candidate_id}/cv")
if cv_response.status_code == 200:
    st.download_button("Download original CV", cv_response.content, file_name=candidate["filename"])

st.write("**HR decision**")
col1, col2, col3 = st.columns(3)
decision = None
if col1.button("Shortlist"):
    decision = "Shortlist"
if col2.button("Review Later"):
    decision = "Review Later"
if col3.button("Reject"):
    decision = "Reject"

if decision:
    requests.put(f"{API_URL}/candidates/{candidate_id}/decision", json={"decision": decision})
    st.rerun()