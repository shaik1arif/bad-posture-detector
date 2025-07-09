from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp
import tempfile
import os
import math

app = FastAPI()

# ✅ Update this with your actual frontend deployment URL
origins = [
    "https://bad-posture-detector-nine.vercel.app",  # your Vercel frontend URL
    "http://localhost:5173"  # optional, for local testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...), posture_type: str = Form(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
            temp.write(await file.read())
            temp_path = temp.name

        cap = cv2.VideoCapture(temp_path)
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        bad_posture_frames = []
        frame_index = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_index += 1

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                try:
                    shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                                landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                    hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                             landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                    toe = [landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x,
                           landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y]

                    back_angle = calculate_angle(shoulder, hip, knee)
                    knee_toe_diff = knee[0] - toe[0]

                    is_bad = False

                    if posture_type == "squat":
                        if back_angle < 150 or knee_toe_diff > 0.03:
                            is_bad = True
                    elif posture_type == "sitting":
                        neck = [landmarks[mp_pose.PoseLandmark.NOSE.value].x,
                                landmarks[mp_pose.PoseLandmark.NOSE.value].y]
                        neck_angle = calculate_angle(shoulder, neck, hip)
                        if back_angle < 150 or neck_angle > 30:
                            is_bad = True

                    if is_bad:
                        bad_posture_frames.append({
                            "frame": frame_index,
                            "back_angle": round(back_angle, 2),
                            "knee_toe_diff": round(knee_toe_diff, 2)
                        })

                except Exception as e:
                    continue

        cap.release()
        os.remove(temp_path)

        return JSONResponse(content={
            "total_checked_frames": frame_index,
            "bad_posture_frames": bad_posture_frames
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
