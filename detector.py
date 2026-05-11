# detector.py
import cv2
import time
import os
import numpy as np
import face_recognition
from camera import Camera
import config, db, utils, notifier
from threading import Lock, Thread

class Detector:
    def __init__(self):
        self.cam = Camera(config.VIDEO_SOURCE)
        self.bg_sub = cv2.createBackgroundSubtractorMOG2(history=500, varThreshold=50, detectShadows=True)
        self.known_encodings, self.known_names = utils.load_known_faces(config.KNOWN_FACES_DIR)
        self.ann_frame = None    # annotated frame for streaming
        self.lock = Lock()
        self.last_alert_time = 0
        self.cooldown = config.COOLDOWN_SECONDS
        self.current_pending = None  # (intrusion_id, image_path)
        Thread(target=self._run, daemon=True).start()

    def reload_known(self):
        self.known_encodings, self.known_names = utils.load_known_faces(config.KNOWN_FACES_DIR)
        print("[Detector] known faces reloaded:", self.known_names)

    def _run(self):
        while True:
            frame = self.cam.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            small = cv2.resize(frame, (0,0), fx=0.5, fy=0.5)
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            fgmask = self.bg_sub.apply(gray)

            # threshold & find contours
            thresh = cv2.threshold(fgmask, 244, 255, cv2.THRESH_BINARY)[1]
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion = False
            for c in contours:
                if cv2.contourArea(c) > config.MOTION_AREA_THRESHOLD:
                    motion = True
                    break

            annotated = frame.copy()

            if motion:
                rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
                face_locs = face_recognition.face_locations(rgb_small)
                if face_locs:
                    face_encs = face_recognition.face_encodings(rgb_small, face_locs)
                    for (top, right, bottom, left), enc in zip(face_locs, face_encs):
                        # scale coords up to original frame
                        top *= 2; right *= 2; bottom *= 2; left *= 2
                        name = "Unknown"
                        if self.known_encodings:
                            dists = face_recognition.face_distance(self.known_encodings, enc)
                            best_idx = np.argmin(dists)
                            if dists[best_idx] < config.FACE_TOLERANCE:
                                name = self.known_names[best_idx]
                        # annotate frame
                        cv2.rectangle(annotated, (left, top), (right, bottom), (0,255,0), 2)
                        cv2.putText(annotated, name, (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,255), 2)

                        if name == "Unknown":
                            now = time.time()
                            if now - self.last_alert_time >= self.cooldown:
                                self.last_alert_time = now
                                # save image
                                os.makedirs(config.SAVE_DIR, exist_ok=True)
                                os.makedirs(config.PENDING_DIR, exist_ok=True)
                                ts = time.strftime("%Y%m%d_%H%M%S")
                                filename = os.path.join(config.PENDING_DIR, f"sentineleye_intruder_{ts}.jpg")
                                cv2.imwrite(filename, frame)
                                # log in DB
                                intrusion_id = db.log_intrusion(config.DB_PATH, filename, "Unknown")
                                self.current_pending = (intrusion_id, filename)
                                # notify (alarm + email thread)
                                notifier.notify_intruder(filename, intrusion_id)
                                print("[Detector] Intruder saved:", filename, "id:", intrusion_id)
                            else:
                                # already alerted recently: skip saving/email
                                pass

            # write annotated frame for streaming
            with self.lock:
                self.ann_frame = annotated

            time.sleep(0.02)

    def get_annotated_frame_jpg(self):
        with self.lock:
            if self.ann_frame is None:
                return None
            _, jpeg = cv2.imencode('.jpg', self.ann_frame)
            return jpeg.tobytes()

    def allow_current_pending(self, name):
        # Move pending image into known_faces/<name>/ and update DB
        if not self.current_pending:
            return None
        intrusion_id, image_path = self.current_pending
        # move into known faces
        dest = utils.add_known_face_from_image(image_path, name, config.KNOWN_FACES_DIR)
        db.update_label(config.DB_PATH, intrusion_id, name)
        self.reload_known()
        self.current_pending = None
        return dest

    def shutdown(self):
        self.cam.release()
