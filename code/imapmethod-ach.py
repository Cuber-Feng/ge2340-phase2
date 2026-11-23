import imaplib
import email
from email.header import decode_header
import time
import json
import os

# Setup
EMAIL = "bulelance9@gmail.com"
APP_PASSWORD = "sijboclwckmsinek"
IMAP_SERVER = "imap.gmail.com"
OUTPUT_FOLDER = "./mail_json"  # Folder to save the JSON files

# Create the output folder if it doesn't exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def get_unread_imap():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, APP_PASSWORD)
    mail.select("INBOX")
    status, data = mail.search(None, "UNSEEN")
    mail_ids = data[0].split()
    result = []
    for mail_id in mail_ids:
        res, msg_data = mail.fetch(mail_id, "(RFC822)")
        msg = email.message_from_bytes(msg_data[0][1])

        # Decode the email subject
        subject_parts = decode_header(msg["Subject"])
        subj = ""
        for part, enc in subject_parts:
            if isinstance(part, bytes):
                subj += part.decode(enc or "utf-8", errors="replace")
            else:
                subj += part

        # Get the sender's email address
        from_ = msg.get("From", "")
        # Get the date of the email
        date_ = msg.get("Date", "")

        # Get the email body (only the first text/plain part)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

        mail_item = {
            "subject": subj,
            "from": from_,
            "date": date_,
            "body": body
        }
        result.append(mail_item)

        # Write to a separate JSON file, named with time + mail_id to avoid duplicates
        filename = f"{time.time()}_{mail_id.decode()}.json"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mail_item, f, ensure_ascii=False, indent=2)

        # Mark the email as read
        mail.store(mail_id, '+FLAGS', '\\Seen')

    mail.close()
    mail.logout()
    return result

# Polling: Check every 60 seconds
while True:
    print("=== Polling The Inbox ===")
    try:
        mails = get_unread_imap()
        for m in mails:
            print("New email saved:", m["subject"])
    except Exception as e:
        print("Error:", e)
    time.sleep(60)
