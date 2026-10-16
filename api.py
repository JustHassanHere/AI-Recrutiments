from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from database import (
    create_tables,
    create_job,
    get_job,
    get_all_jobs,
    update_must_have,
    get_candidates,
    get_candidate,
    update_decision,
)
from gemini_matcher import extract_job_requirements
from screening import run_screening, get_ranking

app = FastAPI(title="AI Recruitment Screening Assistant")
create_tables()

DECISIONS = ["Pending", "Shortlist", "Review Later", "Reject"]


# ---------- Pydantic models ----------
class JobCreate(BaseModel):
    title: str
    description: str


class MustHaveUpdate(BaseModel):
    must_have: list[str]


class DecisionUpdate(BaseModel):
    decision: str


class Requirement(BaseModel):
    category: str
    text: str


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    requirements: list[Requirement]
    must_have: list[str]


class MatchResult(BaseModel):
    requirement: str
    category: str
    status: str
    evidence: str


class CandidateResponse(BaseModel):
    id: int
    job_id: int
    filename: str
    sender: str
    subject: str
    score: float
    qualified: int
    missing_must: list[str]
    decision: str
    results: list[MatchResult]
    cv_info: dict


class CandidatesResponse(BaseModel):
    stats: dict
    qualified: list[CandidateResponse]
    not_qualified: list[CandidateResponse]


# ---------- Jobs ----------
@app.post("/jobs", response_model=JobResponse)
def create_new_job(job: JobCreate):
    if not job.title.strip() or not job.description.strip():
        raise HTTPException(status_code=400, detail="Title and description cannot be empty")

    try:
        requirements = extract_job_requirements(job.description)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"AI extraction failed: {error}")

    job_id = create_job(job.title, job.description, requirements)
    return get_job(job_id)


@app.get("/jobs", response_model=list[JobResponse])
def list_jobs():
    return get_all_jobs()


@app.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(job_id: int):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/jobs/{job_id}/must-have", response_model=JobResponse)
def set_must_have(job_id: int, data: MustHaveUpdate):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    requirement_texts = [r["text"] for r in job["requirements"]]
    for item in data.must_have:
        if item not in requirement_texts:
            raise HTTPException(status_code=400, detail=f"'{item}' is not a requirement of this job")

    update_must_have(job_id, data.must_have)
    return get_job(job_id)


# ---------- Screening ----------
@app.post("/jobs/{job_id}/screen")
def screen_cvs(job_id: int):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        return run_screening(job_id)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Screening failed: {error}")


# ---------- Candidates ----------
@app.get("/jobs/{job_id}/candidates", response_model=CandidatesResponse)
def read_candidates(job_id: int, top_n: int = 20):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    qualified, not_qualified, qualified_total = get_ranking(job_id, top_n)
    all_candidates = get_candidates(job_id)

    stats = {
        "total": len(all_candidates),
        "qualified": qualified_total,
        "not_qualified": len(not_qualified),
        "shortlist": len([c for c in all_candidates if c["decision"] == "Shortlist"]),
        "review_later": len([c for c in all_candidates if c["decision"] == "Review Later"]),
        "reject": len([c for c in all_candidates if c["decision"] == "Reject"]),
    }

    return {"stats": stats, "qualified": qualified, "not_qualified": not_qualified}


@app.put("/candidates/{candidate_id}/decision")
def set_decision(candidate_id: int, data: DecisionUpdate):
    if data.decision not in DECISIONS:
        raise HTTPException(status_code=400, detail=f"Decision must be one of {DECISIONS}")

    candidate = get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    update_decision(candidate_id, data.decision)
    return {"id": candidate_id, "decision": data.decision}


@app.get("/candidates/{candidate_id}/cv")
def download_cv(candidate_id: int):
    candidate = get_candidate(candidate_id)
    if candidate is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    if not Path(candidate["file_path"]).exists():
        raise HTTPException(status_code=404, detail="CV file not found on disk")

    return FileResponse(candidate["file_path"], filename=candidate["filename"])