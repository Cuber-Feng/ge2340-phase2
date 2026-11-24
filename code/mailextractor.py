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
INDEX_PATH = r"./saved_uids.json"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def load_saved_uids():
    """从本地索引和已有 json 恢复已保存的 UID，重启后也不会重复写入。"""
    uids = set()
    if os.path.exists(INDEX_PATH):
        try:
            with open(INDEX_PATH, encoding="utf-8") as f:
                data = json.load(f)
            uids.update(str(item) for item in data)
        except (OSError, json.JSONDecodeError):
            pass

    for name in os.listdir(OUTPUT_FOLDER):
        if not name.endswith(".json") or name.startswith("_"):
            continue
        path = os.path.join(OUTPUT_FOLDER, name)
        try:
            with open(path, encoding="utf-8") as f:
                item = json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
        uid = item.get("uid")
        if uid:
            uids.add(str(uid))
    return uids


def save_saved_uids(uids):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(uids), f, ensure_ascii=False, indent=2)


def decode_mime(value):
    if not value:
        return ""
    text = ""
    for part, enc in decode_header(value):
        if isinstance(part, bytes):
            text += part.decode(enc or "utf-8", errors="replace")
        else:
            text += part or ""
    return text


def extract_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            disposition = (part.get("Content-Disposition") or "").lower()
            if part.get_content_type() != "text/plain" or "attachment" in disposition:
                continue
            payload = part.get_payload(decode=True)
            if payload:
                charset = part.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return ""

    payload = msg.get_payload(decode=True)
    if not payload:
        return ""
    charset = msg.get_content_charset() or "utf-8"
    return payload.decode(charset, errors="replace")


def message_bytes(msg_data):
    if not msg_data or msg_data[0] is None:
        return None
    for item in msg_data:
        if isinstance(item, tuple) and len(item) >= 2 and isinstance(item[1], (bytes, bytearray)):
            return bytes(item[1])
    return None


def stable_hash(msg, subj, from_, date_, body):
    """同一封邮件每次运行都得到同一个摘要。优先用 Message-ID。"""
    message_id = (msg.get("Message-ID") or "").strip()
    if message_id:
        raw = message_id
    else:
        raw = "\n".join([from_, date_, subj, body])
    return hashlib.sha256(raw.encode("utf-8", errors="replace")).hexdigest()


def get_all_mail(saved_uids):
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    try:
        mail.login(EMAIL, APP_PASSWORD)
        # 只读打开，服务器不会因为这次读取改已读/未读等状态
        mail.select("INBOX", readonly=True)
        status, data = mail.uid("SEARCH", None, "ALL")
        if status != "OK" or not data or not data[0]:
            return []

        result = []
        changed = False
        for uid_bytes in data[0].split():
            uid = uid_bytes.decode()
            if uid in saved_uids:
                continue

            # BODY.PEEK 只取内容，不会把邮件标成已读
            res, msg_data = mail.uid("FETCH", uid, "(BODY.PEEK[])")
            raw = message_bytes(msg_data)
            if raw is None:
                print("读取失败：", uid)
                continue

            msg = email.message_from_bytes(raw)
            subj = decode_mime(msg.get("Subject"))
            from_ = decode_mime(msg.get("From"))
            date_ = msg.get("Date", "") or ""
            body = extract_body(msg)
            hashcode = stable_hash(msg, subj, from_, date_, body)

            mail_item = {
                "uid": uid,
                "message_id": (msg.get("Message-ID") or "").strip(),
                "subject": subj,
                "from": from_,
                "date": date_,
                "body": body,
            }
            result.append(mail_item)

            file_path = os.path.join(OUTPUT_FOLDER, f"{hashcode}.json")
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(mail_item, f, ensure_ascii=False, indent=2)
                print("已保存邮件：", uid, subj)
            else:
                print("已存在，跳过：", uid, subj)

            saved_uids.add(uid)
            changed = True

        if changed:
            save_saved_uids(saved_uids)
        return result
    finally:
        try:
            mail.logout()
        except Exception:
            pass


saved_uids = load_saved_uids()

while True:
    print("=== 扫描全部邮件 ===")
    try:
        get_all_mail(saved_uids)
    except Exception as e:
        print("出错：", e)
    time.sleep(300)
