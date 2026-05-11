# config.py
import os
from dotenv import load_dotenv
from db import init_db   # ✅ use your db initializer

# Load environment variables from .env
load_dotenv()

# Project info
PROJECT_NAME = "SentinelEye 👁️"

# Email settings (from .env file)
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_APP_PASSWORD = os.getenv("SENDER_APP_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))

# Files / folders
REGISTERED_EMAILS_FILE = "sentineleye_registered_emails.json"
SAVE_DIR = "sentineleye_captures"
KNOWN_FACES_DIR = "known_faces"
PENDING_DIR = "pending"

# Database
DB_PATH = os.getenv("DB_PATH", "sentineleye.db")

# Sound alerts
ALERT_SOUND = os.getenv("ALERT_SOUND", "siren-alert-96052.mp3")

# Flask security
SECRET_KEY = os.getenv("SECRET_KEY", "shivam123")

# Behavior tuning
COOLDOWN_SECONDS = 60              # seconds between email alerts
FACE_TOLERANCE = 0.45              # face_recognition tolerance
MOTION_AREA_THRESHOLD = 800        # contour area to count as motion (tune)
VIDEO_SOURCE = 0                   # 0 for laptop webcam

# ✅ Ensure folders exist
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs(KNOWN_FACES_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)

# ✅ Initialize database (creates sentineleye.db if missing)
init_db(DB_PATH)
