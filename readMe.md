# AI Recruitment Screening Assistant

Helps HR screen CVs faster. The system reads CVs from Gmail, compares them with the
job requirements, separates candidates who miss a Must-Have requirement, and ranks the rest.
HR makes the final decision (Shortlist / Review Later / Reject).

## Technologies
Python, Gmail API, pypdf, python-docx, Gemini API, SQLite, Pandas, FastAPI, Pydantic, Uvicorn, Streamlit, Requests

## Installation
1. Create and activate a virtual environment
2. `pip install -r requirements.txt`

## Configuration
1. Create a Google Cloud project, enable Gmail API, and download `credentials.json` (read-only scope) into the project folder
2. Create a `.env` file:
   GEMINI_API_KEY=your_key
   GEMINI_MODEL=gemini-2.5-flash
3. Run `python screening.py` once to log in to Gmail and create the token

## Run
1. Backend: `uvicorn api:app --reload`
2. Interface (new terminal): `streamlit run Home.py`
3. Tests: `python test_api.py`

## Usage
1. Create Job: enter the description, review the extracted requirements, choose Must-Have
2. Screening: start the CV screening
3. Candidates: review ranking, evidence, original CV, and mark each candidate

## Notes
Never commit `.env`, `credentials.json`, or the Gmail token.
