import os
import database

# use a separate test database
database.DB_NAME = "test_recruitment.db"

from fastapi.testclient import TestClient
from docx import Document
from api import app
from database import create_job, save_candidate, get_candidates
from gemini_matcher import calculate_score
from cv_text_extractor import extract_cv_text

client = TestClient(app)


def make_results(python_status, sql_status):
    return [
        {"requirement": "Python", "category": "skills", "status": python_status, "evidence": "x"},
        {"requirement": "SQL", "category": "skills", "status": sql_status, "evidence": "x"},
    ]


def test_invalid_job():
    assert client.post("/jobs", json={"title": "", "description": "abc"}).status_code == 400
    assert client.post("/jobs", json={"title": "abc"}).status_code == 422
    assert client.get("/jobs/9999").status_code == 404
    assert client.post("/jobs/9999/screen").status_code == 404
    assert client.put("/jobs/9999/must-have", json={"must_have": []}).status_code == 404


def test_must_have():
    job_id = create_job("Test Job", "desc", [
        {"category": "skills", "text": "Python"},
        {"category": "skills", "text": "SQL"},
    ])
    ok = client.put(f"/jobs/{job_id}/must-have", json={"must_have": ["Python"]})
    assert ok.status_code == 200
    bad = client.put(f"/jobs/{job_id}/must-have", json={"must_have": ["Java"]})
    assert bad.status_code == 400
    return job_id


def test_score_and_filter():
    score, qualified, missing = calculate_score(make_results("Meets", "Does Not Meet"), ["Python"])
    assert score == 50.0 and qualified == 1 and missing == []
    score, qualified, missing = calculate_score(make_results("Does Not Meet", "Meets"), ["Python"])
    assert qualified == 0 and missing == ["Python"]


def test_ranking_duplicates_and_decision():
    job_id = test_must_have()

    save_candidate(job_id, "m1", "a.pdf", "downloads/a.pdf", "a@x.com", "Hi", {}, make_results("Meets", "Meets"))
    save_candidate(job_id, "m2", "b.pdf", "downloads/b.pdf", "b@x.com", "Hi", {}, make_results("Does Not Meet", "Meets"))
    save_candidate(job_id, "m1", "a.pdf", "downloads/a.pdf", "a@x.com", "Hi", {}, make_results("Meets", "Meets"))  # duplicate

    assert len(get_candidates(job_id)) == 2  # duplicate was ignored

    data = client.get(f"/jobs/{job_id}/candidates").json()
    assert len(data["qualified"]) == 1
    assert len(data["not_qualified"]) == 1
    assert data["qualified"][0]["filename"] == "a.pdf"

    candidate_id = data["qualified"][0]["id"]
    assert client.put(f"/candidates/{candidate_id}/decision", json={"decision": "Shortlist"}).status_code == 200
    assert client.put(f"/candidates/{candidate_id}/decision", json={"decision": "Maybe"}).status_code == 400
    assert client.put("/candidates/9999/decision", json={"decision": "Reject"}).status_code == 404


def test_extraction():
    doc = Document()
    doc.add_paragraph("John - Python Developer")
    doc.save("test_cv.docx")
    assert "Python" in extract_cv_text("test_cv.docx")
    os.remove("test_cv.docx")

    try:
        extract_cv_text("cv.txt")
        assert False
    except ValueError:
        pass


if __name__ == "__main__":
    test_invalid_job()
    test_score_and_filter()
    test_ranking_duplicates_and_decision()
    test_extraction()
    print("All tests passed")
    if os.path.exists("test_recruitment.db"):
        os.remove("test_recruitment.db")