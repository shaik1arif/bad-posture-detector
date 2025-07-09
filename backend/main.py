from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp
import tempfile
import math

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with your Vercel frontend URL for better security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(static_image_mode=False)

def calculate_angle(p1, p2, p3):
    a = np.array(p1)
    b = np.array(p2)
    c = np.array(p3)
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    if angle > 180.0:
        angle = 360 - angle
    return angle

@app.post("/upload-video")
async def upload_video(file: UploadFile = File(...), posture_type: str = Form(...)):
    contents = await file.read()

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        temp_file.write(contents)
        video_path = temp_file.name

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return JSONResponse(status_code=400, content={"error": "Cannot read video"})

    bad_posture_frames = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if not results.pose_landmarks:
            continue

        landmarks = results.pose_landmarks.landmark

        if posture_type == "squat":
            try:
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                        landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                         landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
                toe = [landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y]

                back_angle = calculate_angle(shoulder:=landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, hip, knee)
                knee_toe_diff = knee[0] - toe[0]

                if back_angle < 150 or knee_toe_diff > 0.03:
                    bad_posture_frames.append({
                        "frame": frame_count,
                        "back_angle": back_angle,
                        "knee_toe_diff": knee_toe_diff
                    })

            except Exception as e:
                continue

        elif posture_type == "sitting":
            try:
                shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                            landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
                ear = [landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_EAR.value].y]
                hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                neck_angle = calculate_angle(ear, shoulder, hip)
                if neck_angle < 150:
                    bad_posture_frames.append({
                        "frame": frame_count,
                        "neck_angle": neck_angle
                    })

            except Exception as e:
                continue

    cap.release()
    return {
        "total_checked_frames": frame_count,
        "bad_posture_frames": bad_posture_frames
    }
