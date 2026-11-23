import imaplib
import email
from email.header import decode_header
import hashlib
import time
import json
import os

# 配置
EMAIL = "bulelance9@gmail.com"
APP_PASSWORD = "sijboclwckmsinek"
IMAP_SERVER = "imap.gmail.com"
OUTPUT_FOLDER = "./mail_json"
# 记录已经保存过的邮件id，防止重复写入
saved_ids = set()

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def stable_hash(msg, subj, from_, date_, body):
    """同一封邮件每次运行都得到同一个摘要。优先用 Message-ID。"""
    message_id = (msg.get("Message-ID") or "").strip()
    if message_id:
        raw = message_id
    else:
        raw = "\n".join([from_, date_, subj, body])
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()

def get_all_mail():
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, APP_PASSWORD)
    # 只读打开，服务器不会因为这次读取改已读/未读等状态
    mail.select("INBOX", readonly=True)
    # 读取全部邮件，不再只看未读
    status, data = mail.search(None, "ALL")
    mail_ids = data[0].split()
    result = []

    for mail_id in mail_ids:
        mid = mail_id.decode()
        if mid in saved_ids:
            continue  # 已经保存过，跳过

        # BODY.PEEK 只取内容，不会把邮件标成已读
        res, msg_data = mail.fetch(mail_id, "(BODY.PEEK[])")
        msg = email.message_from_bytes(msg_data[0][1])

        # 解码主题
        subject_parts = decode_header(msg["Subject"])
        subj = ""
        for part, enc in subject_parts:
            if isinstance(part, bytes):
                subj += part.decode(enc or "utf-8", errors="replace")
            else:
                subj += part

        from_ = msg.get("From", "")
        date_ = msg.get("Date", "")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

        mail_item = {
            "mail_id": mid,
            "subject": subj,
            "from": from_,
            "date": date_,
            "body": body
        }
        result.append(mail_item)

        hashcode = stable_hash(msg, subj, from_, date_, body)
        filename = f"{hashcode}.json"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        if not os.path.exists(file_path):
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(mail_item, f, ensure_ascii=False, indent=2)
            print("已保存邮件：", mid, subj)
        else:
            print("已存在，跳过：", mid, subj)

        saved_ids.add(mid)

    mail.close()
    mail.logout()
    return result

# 轮询
while True:
    print("=== 扫描全部邮件 ===")
    try:
        get_all_mail()
    except Exception as e:
        print("出错：", e)
    time.sleep(300)
