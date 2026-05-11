# notifier.py
import threading
import os
import smtplib
from email.message import EmailMessage
from playsound import playsound
import config
import db

def _play_alarm():
    # non-blocking call
    try:
        # put an alarm.mp3 at project root, or remove this call if you don't want sound
        if os.path.exists("alarm.mp3"):
            playsound("alarm.mp3")
    except Exception as e:
        print("Alarm error:", e)

def _send_email(subject, body, attachment_path, recipients):
    try:
        msg = EmailMessage()
        msg["From"] = config.SENDER_EMAIL
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.set_content(body)

        with open(attachment_path, "rb") as f:
            data = f.read()
            ext = os.path.splitext(attachment_path)[1].lower().lstrip(".")
            subtype = "jpeg" if ext in ("jpg","jpeg") else (ext or "octet-stream")
            msg.add_attachment(data, maintype="image", subtype=subtype, filename=os.path.basename(attachment_path))

        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT) as smtp:
            smtp.login(config.SENDER_EMAIL, config.SENDER_APP_PASSWORD)
            smtp.send_message(msg)
        return True, None
    except Exception as e:
        return False, str(e)

def notify_intruder(image_path, intrusion_id):
    # play alarm (thread)
    threading.Thread(target=_play_alarm, daemon=True).start()

    # load recipients list file
    import json
    recipients = []
    if os.path.exists(config.REGISTERED_EMAILS_FILE):
        try:
            with open(config.REGISTERED_EMAILS_FILE, "r") as f:
                recipients = json.load(f)
        except:
            recipients = []

    if not recipients:
        print("No registered emails, skipping email send.")
        return

    subject = f"SentinelEye Alert: Stranger has been detected"
    body = f"SentinelEye detected a stranger. Entry id: {intrusion_id}."

    def _send_and_mark():
        ok, err = _send_email(subject, body, image_path, recipients)
        if ok:
            db.mark_emailed(config.DB_PATH, intrusion_id)
            print("Email sent for intrusion", intrusion_id)
        else:
            print("Email error:", err)

    threading.Thread(target=_send_and_mark, daemon=True).start()
