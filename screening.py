import pandas as pd

from gmail_reader import search_emails, get_email_details, get_header
from attachment_downloader import get_cv_attachments, save_attachment
from cv_text_extractor import extract_cv_text
from gemini_matcher import (
    extract_job_requirements,
    extract_cv_info,
    match_cv_to_requirements,
    calculate_score,
)
from database import (
    create_tables,
    create_job,
    get_job,
    get_all_jobs,
    update_must_have,
    candidate_exists,
    save_candidate,
    get_candidates,
)

MAX_RESULTS = 5
DOWNLOAD_DIR = "downloads"
USE_SUBJECT_FILTER = True  # only read emails that have the job title in the subject

# sample job, used only when you run screening.py and there is no job in the database yet
JOB_TITLE = "Python Developer"
JOB_DESCRIPTION = """
We are looking for a Python Developer.
Required skills: Python, SQL, Git, Django, REST API.
Experience: at least 2 years of experience in backend development.
Education: Bachelor's degree in Computer Science or a related field.
Languages: English.
Nice to have: Docker.
"""


def run_screening(job_id):
    job = get_job(job_id)
    if job is None:
        raise ValueError("Job not found")

    query = "has:attachment (filename:pdf OR filename:docx)"
    if USE_SUBJECT_FILTER:
        query += f' subject:"{job["title"]}"'

    messages = search_emails(query, MAX_RESULTS)

    new_count = 0
    skipped_count = 0
    error_count = 0

    for message in messages:
        message_id = message["id"]

        try:
            email = get_email_details(message_id)
        except Exception as error:
            print(f"Could not read email {message_id}: {error}")
            error_count += 1
            continue

        headers = email.get("payload", {}).get("headers", [])
        subject = get_header(headers, "Subject")
        sender = get_header(headers, "From")

        attachments = get_cv_attachments(email)
        if not attachments:
            print(f"No CV attachments in email: {subject}")
            continue

        for attachment in attachments:
            # avoid processing the same email/CV twice
            if candidate_exists(job_id, message_id, attachment["filename"]):
                print(f"Already processed: {attachment['filename']}")
                skipped_count += 1
                continue

            try:
                # message id in the file name so two CVs called "CV.pdf" do not overwrite each other
                saved_attachment = dict(attachment)
                saved_attachment["filename"] = message_id + "_" + attachment["filename"]
                file_path = save_attachment(message_id, saved_attachment, DOWNLOAD_DIR)

                cv_text = extract_cv_text(str(file_path))
                if not cv_text.strip():
                    print(f"No text found in {file_path}")
                    error_count += 1
                    continue

                cv_info = extract_cv_info(cv_text)
                results = match_cv_to_requirements(cv_text, job["requirements"])

                save_candidate(
                    job_id,
                    message_id,
                    attachment["filename"],
                    file_path,
                    sender,
                    subject,
                    cv_info,
                    results,
                )
                new_count += 1
                print(f"Processed: {attachment['filename']}")

            except Exception as error:
                # one bad file should not stop the whole workflow
                print(f"Error with {attachment['filename']}: {error}")
                error_count += 1

    return {"new": new_count, "skipped": skipped_count, "errors": error_count}


def get_ranking(job_id, top_n=20):
    job = get_job(job_id)
    candidates = get_candidates(job_id)

    if not candidates:
        return [], [], 0

    for candidate in candidates:
        score, qualified, missing_must = calculate_score(candidate["results"], job["must_have"])
        candidate["score"] = score
        candidate["qualified"] = qualified
        candidate["missing_must"] = missing_must

    df = pd.DataFrame(candidates)

    qualified_df = df[df["qualified"] == 1].sort_values("score", ascending=False)
    not_qualified_df = df[df["qualified"] == 0].sort_values("score", ascending=False)

    qualified_total = len(qualified_df)
    qualified_list = qualified_df.head(top_n).to_dict("records")
    not_qualified_list = not_qualified_df.to_dict("records")

    return qualified_list, not_qualified_list, qualified_total


def main():
    create_tables()

    jobs = get_all_jobs()
    if jobs:
        job_id = jobs[-1]["id"]  # the latest job
    else:
        requirements = extract_job_requirements(JOB_DESCRIPTION)
        job_id = create_job(JOB_TITLE, JOB_DESCRIPTION, requirements)

    job = get_job(job_id)

    if not job["requirements"]:
        print("No requirements were found for this job.")
        print("Delete recruitment.db and run again.")
        return

    if not job["must_have"]:
        must_have = [r["text"] for r in job["requirements"] if r["category"] == "skills"]
        update_must_have(job_id, must_have)
        job = get_job(job_id)

    print(f"Job: {job['title']}")
    print(f"Must-Have: {', '.join(job['must_have'])}")
    print("-" * 50)

    stats = run_screening(job_id)
    print(f"New: {stats['new']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}")
    print("-" * 50)

    qualified, not_qualified, qualified_total = get_ranking(job_id)

    print(f"Qualified candidates: {qualified_total}")
    for candidate in qualified:
        print(f"{candidate['filename']} - {candidate['score']}% - {candidate['sender']}")

    print("-" * 50)
    print("Missing a Must-Have:")
    for candidate in not_qualified:
        print(f"{candidate['filename']} - {candidate['score']}% - missing: {', '.join(candidate['missing_must'])}")


if __name__ == "__main__":
    main()