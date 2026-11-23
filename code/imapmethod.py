import imaplib
import email
from email.header import decode_header
import time
import json
import os

# 配置
EMAIL = "bulelance9@gmail.com"
APP_PASSWORD = "sijboclwckmsinek"
IMAP_SERVER = "imap.gmail.com"
OUTPUT_FOLDER = "./mail_json"  # 输出json的文件夹

# 文件夹不存在就自动创建
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

        # 解码主题（修复多段标题报错）
        subject_parts = decode_header(msg["Subject"])
        subj = ""
        for part, enc in subject_parts:
            if isinstance(part, bytes):
                subj += part.decode(enc or "utf-8", errors="replace")
            else:
                subj += part

        # 提取发件人
        from_ = msg.get("From", "")
        # 提取时间
        date_ = msg.get("Date", "")

        # 拿正文
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

        # 写入单独json文件，用时间+邮件id命名，避免重名
        filename = f"{time.time()}_{mail_id.decode()}.json"
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(mail_item, f, ensure_ascii=False, indent=2)

        # 标记已读，防止重复抓取
        mail.store(mail_id, '+FLAGS', '\\Seen')

    mail.close()
    mail.logout()
    return result

# 轮询循环：每300秒(5分钟)查一次
while True:
    print("=== 轮询收件箱 ===")
    try:
        mails = get_unread_imap()
        for m in mails:
            print("已保存新邮件：", m["subject"])
    except Exception as e:
        print("出错：", e)
    time.sleep(60)
