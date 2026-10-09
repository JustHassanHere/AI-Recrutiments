from gmail_reader import search_emails, get_email_details, get_header
from attachment_downloader import get_cv_attachments, save_attachment
from cv_text_extractor import extract_cv_text
from job_matcher import match_cv_to_job

SEARCH_QUERY = "has:attachment (filename:pdf OR filename:docx)"
MAX_RESULTS = 5
DOWNLOAD_DIR = "downloads"

JOB_TITLE = "Python Developer"
JOB_SKILLS = [
    "python",
    "sql",
    "git",
    "docker",
    "django",
    "rest api",
]


def main():
    messages = search_emails(SEARCH_QUERY, MAX_RESULTS)

    if not messages:
        print("No emails found.")
        return

    results = []

    for message in messages:
        message_id = message["id"]
        email = get_email_details(message_id)

        headers = email.get("payload", {}).get("headers", [])
        subject = get_header(headers, "Subject")
        sender = get_header(headers, "From")

        attachments = get_cv_attachments(email)

        if not attachments:
            print(f"No CV attachments in email: {subject}")
            continue

        for attachment in attachments:
            file_path = save_attachment(message_id, attachment, DOWNLOAD_DIR)

            try:
                cv_text = extract_cv_text(str(file_path))
            except Exception as error:
                print(f"Could not read {file_path}: {error}")
                continue

            if not cv_text.strip():
                print(f"No text found in {file_path}")
                continue

            match = match_cv_to_job(cv_text, JOB_SKILLS)

            results.append({
                "filename": attachment["filename"],
                "subject": subject,
                "sender": sender,
                "score": match["score"],
                "matched_skills": match["matched_skills"],
                "missing_skills": match["missing_skills"],
            })

    if not results:
        print("No CVs were matched.")
        return

    results.sort(key=lambda result: result["score"], reverse=True)

    print(f"\nJob: {JOB_TITLE}")
    print(f"Required skills: {', '.join(JOB_SKILLS)}")
    print("-" * 50)

    for result in results:
        print(f"File: {result['filename']}")
        print(f"From: {result['sender']}")
        print(f"Subject: {result['subject']}")
        print(f"Score: {result['score']}%")
        print(f"Matched: {', '.join(result['matched_skills'])}")
        print(f"Missing: {', '.join(result['missing_skills'])}")
        print("-" * 50)


if __name__ == "__main__":
    main()