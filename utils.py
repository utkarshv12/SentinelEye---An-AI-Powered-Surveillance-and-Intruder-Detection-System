# utils.py
import os
import shutil
import face_recognition

def load_known_faces(known_dir):
    encodings = []
    names = []
    if not os.path.exists(known_dir):
        os.makedirs(known_dir, exist_ok=True)
        return encodings, names

    for person in os.listdir(known_dir):
        person_folder = os.path.join(known_dir, person)
        if not os.path.isdir(person_folder):
            continue
        for img in os.listdir(person_folder):
            path = os.path.join(person_folder, img)
            try:
                image = face_recognition.load_image_file(path)
                encs = face_recognition.face_encodings(image)
                if len(encs) > 0:
                    encodings.append(encs[0])
                    names.append(person)
            except Exception as e:
                print("Error loading", path, e)
    return encodings, names

def add_known_face_from_image(image_path, name, known_dir):
    # Create dir and move the image in there (used when allowing an intruder)
    person_folder = os.path.join(known_dir, name)
    os.makedirs(person_folder, exist_ok=True)
    base = os.path.basename(image_path)
    dest = os.path.join(person_folder, base)
    shutil.move(image_path, dest)
    return dest
