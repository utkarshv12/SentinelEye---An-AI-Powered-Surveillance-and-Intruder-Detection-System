# app.py
from flask import Flask, Response, render_template, request, redirect, url_for, jsonify
from detector import Detector
import db, config, os
import threading

app = Flask(__name__, template_folder="templates", static_folder="static")
db.init_db(config.DB_PATH)

det = Detector()  # starts camera + detector thread

@app.route("/")
def index():
    rows = db.fetch_recent(config.DB_PATH, limit=20)
    pending = None
    if det.current_pending:
        pending = {"id": det.current_pending[0], "path": det.current_pending[1]}
    return render_template("index.html", project=config.PROJECT_NAME, rows=rows, pending=pending)

def gen():
    while True:
        jpg = det.get_annotated_frame_jpg()
        if jpg is None:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpg + b'\r\n')
@app.route("/video_feed")
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route("/allow", methods=["POST"])
def allow():
    name = request.form.get("name", "").strip()
    intrusion_id = request.form.get("intrusion_id", "")
    if not name or not intrusion_id:
        return redirect(url_for("index"))
    # allow -> move file, update DB, reload known faces
    dest = det.allow_current_pending(name)
    return redirect(url_for("index"))

@app.route("/register_email", methods=["POST"])
def register_email():
    import json
    email = request.form.get("email", "").strip()
    if not email:
        return redirect(url_for("index"))
    if not os.path.exists(config.REGISTERED_EMAILS_FILE):
        with open(config.REGISTERED_EMAILS_FILE, "w") as f:
            json.dump([email], f)
    else:
        with open(config.REGISTERED_EMAILS_FILE, "r+") as f:
            try:
                arr = json.load(f)
            except:
                arr = []
            if email not in arr:
                arr.append(email)
                f.seek(0); f.truncate(); json.dump(arr, f)
    return redirect(url_for("index"))

if __name__ == "__main__":
    # Run Flask app
    # For mobile access on same network, use host="0.0.0.0"
    app.run(host="0.0.0.0", port=5000, threaded=True)
