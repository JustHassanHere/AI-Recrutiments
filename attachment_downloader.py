import base64
from pathlib import Path

from gmail_service import get_gmail_service

SUPPORTED_MIN_TYPES = {
    "application/pdf" : ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document" : ".docx",
}
SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
def walk_parts(payload):
    yield payload
    for part in payload.get("parts", [] or []):
        yield from walk_parts(part)

def is_supported_cv(filename, mime_type):
    extension = Path(filename).suffix.lower()
    return (
        extension in SUPPORTED_EXTENSIONS
        or mime_type in SUPPORTED_MIN_TYPES
    )

def get_cv_attachments(message):
    payload = message.get("payload" , {})
    attachments = []
    for part in walk_parts(payload):
        filename = part.get("filename")
        mime_type = part.get("mimeType")
        body = part.get("body", {})
        attachment_id = body.get("attachmentId")

        if not filename or not mime_type or not attachment_id:
            continue
        if not is_supported_cv(filename, mime_type):
            continue
        attachments.append({
            "filename": filename,
            "mime_type": mime_type,
            "attachment_id": attachment_id,
        })
    return attachments

def download_attachment(message_id, attachment_id):
    service = get_gmail_service()
    attachment = (
        service.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=message_id, id=attachment_id)
        .execute()
    )
    data = attachment.get("data")
    if not data:
        raise ValueError("Gmail returned an attachment with no data")

    data += "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data.encode("utf-8"))

def save_attachment(message_id , attachment , output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True , exist_ok =True)
    filename = Path(attachment["filename"]).name
    save_path = output_path / filename

    if save_path.exists():
        print(f"File {save_path} already exists. Skipping download.")
        return save_path

    file_bytes = download_attachment(message_id, attachment["attachment_id"],
                                        )
    save_path.write_bytes(file_bytes)
    print(f"Downloaded to {save_path}")
    return save_path