from gmail_service import get_gmail_service


def search_emails(query , max_result = 5):
   service = get_gmail_service()
   response = (
    service.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_result)
        .execute()
   )
   return response.get("messages", [])

def get_email_details(message_id):
   service = get_gmail_service()
   return (
    service.users()
        .messages() 
        .get(userId="me", id=message_id , format="full")
        .execute()
   )
def get_header(headers , name):
    for header in headers:
      if header.get("name","").lower() == name.lower():
         return header.get("value")
    return ""