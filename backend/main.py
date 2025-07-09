from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp
import os
import tempfile
import math

app = FastAPI()

# Allow CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict to your frontend domain for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...), posture_type: str = Form(...)):
    try:
        # Save uploaded video temporarily
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)

        with open(file_path, "wb") as f:
            f.write(await file.read())

        cap = cv2.VideoCapture(file_path)

        pose = mp_pose.Pose(static_image_mode=False)
        total_frames = 0
        bad_posture_frames = []

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            total_frames += 1
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(image)

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark

                # Extract required landmarks
                left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
                left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
                left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
                left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
                left_heel = landmarks[mp_pose.PoseLandmark.LEFT_HEEL]
                left_toe = landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX]

                # Calculate back angle
                back_angle = calculate_angle(left_shoulder, left_hip, left_knee)

                # Calculate horizontal distance between knee and toe
                knee_toe_diff = left_knee.x - left_toe.x

                # Debug print
                print(f"Frame {total_frames}: Back Angle = {back_angle:.2f}, Knee-Toe Diff = {knee_toe_diff:.2f}")

                # Classification logic
                is_bad_posture = False
                if posture_type == "squat":
                    if back_angle < 135 or abs(knee_toe_diff) > 0.03:
                        is_bad_posture = True
                elif posture_type == "sitting":
                    if back_angle < 95:
                        is_bad_posture = True

                if is_bad_posture:
                    print(f"❗ Bad posture detected in frame {total_frames}")
                    bad_posture_frames.append({
                        "frame": total_frames,
                        "back_angle": back_angle,
                        "knee_toe_diff": knee_toe_diff
                    })

        cap.release()

        return JSONResponse(content={
            "total_checked_frames": total_frames,
            "bad_posture_frames": bad_posture_frames
        })

    except Exception as e:
        print("❌ Error processing video:", str(e))
        return JSONResponse(status_code=500, content={"error": str(e)})

def calculate_angle(a, b, c):
    a = np.array([a.x, a.y])
    b = np.array([b.x, b.y])
    c = np.array([c.x, c.y])

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return math.degrees(angle)
