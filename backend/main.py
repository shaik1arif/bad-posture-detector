from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import mediapipe as mp
import numpy as np
import tempfile
import os

app = FastAPI()

# Allow frontend to call backend (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Backend is working!"}

@app.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    posture_type: str = Form(...)
):
    if posture_type not in ["squat", "sitting"]:
        return JSONResponse(status_code=400, content={"error": "Invalid posture type"})

    # Save uploaded video to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
        temp.write(await file.read())
        video_path = temp.name

    # Initialize MediaPipe
    mp_pose = mp.solutions.pose
    pose = mp_pose.Pose()
    cap = cv2.VideoCapture(video_path)

    bad_posture_frames = []
    frame_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_num += 1

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            # Extract needed keypoints
            shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
            hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
            knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
            ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
            ear = landmarks[mp_pose.PoseLandmark.LEFT_EAR]

            # Compute angles/distances
            back_angle = calculate_angle(
                [shoulder.x, shoulder.y],
                [hip.x, hip.y],
                [knee.x, knee.y]
            )

            knee_toe_diff = knee.x - ankle.x
            neck_angle = calculate_angle(
                [ear.x, ear.y],
                [shoulder.x, shoulder.y],
                [hip.x, hip.y]
            )

            is_bad = False

            if posture_type == "squat":
                if back_angle < 150 or knee_toe_diff > 0:
                    is_bad = True
            elif posture_type == "sitting":
                if back_angle < 160 or neck_angle < 150:
                    is_bad = True

            if is_bad:
                bad_posture_frames.append({
                    "frame": frame_num,
                    "back_angle": back_angle,
                    "knee_toe_diff": knee_toe_diff,
                })

    cap.release()
    os.remove(video_path)

    return {
        "total_checked_frames": frame_num,
        "bad_posture_frames": bad_posture_frames
    }

def calculate_angle(a, b, c):
    """Calculate angle at point b given three points a, b, c."""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    ba = a - b
    bc = c - b

    cosine_angle = np.dot(ba, bc) / (
        np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8
    )
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)
