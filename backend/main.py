from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import cv2
import numpy as np
import mediapipe as mp
import os
import tempfile

app = FastAPI()

# ✅ Allow CORS for your deployed frontend (Vercel)
origins = [
    "https://bad-posture-detector-18qmv911r-shaik1arifs-projects.vercel.app",
    "http://localhost:5173",  # Optional for local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Use ["*"] if testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def calculate_angle(a, b, c):
    """Calculate the angle between three points"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    ba = a - b
    bc = c - b
    
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    
    return np.degrees(angle)

def process_video(file_path, posture_type):
    cap = cv2.VideoCapture(file_path)
    bad_frames = []
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_count += 1

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            # Common keypoints
            shoulder = [lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        lm[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [lm[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                   lm[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [lm[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    lm[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                     lm[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            toe = [lm[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].x,
                   lm[mp_pose.PoseLandmark.LEFT_FOOT_INDEX.value].y]

            back_angle = calculate_angle(shoulder, hip, knee)
            knee_toe_diff = knee[0] - toe[0]

            # Simple rule-based conditions for bad posture
            is_bad = False
            if posture_type == "squat":
                if back_angle > 130 or knee_toe_diff < -0.05:
                    is_bad = True
            elif posture_type == "sitting":
                if back_angle > 120:
                    is_bad = True

            if is_bad:
                print(f"❗ Bad posture detected in frame {frame_count}")
                bad_frames.append({
                    "frame": frame_count,
                    "back_angle": round(back_angle, 2),
                    "knee_toe_diff": round(knee_toe_diff, 4)
                })
            else:
                print(f"✅ Good posture in frame {frame_count}")
        else:
            print(f"⚠️ No person detected in frame {frame_count}")

    cap.release()
    return {
        "total_checked_frames": frame_count,
        "bad_posture_frames": bad_frames
    }

@app.post("/upload-video")
async def upload_video(
    file: UploadFile = File(...),
    posture_type: str = Form(...)
):
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name

        print(f"📥 Video saved to temp path: {tmp_path}")
        result = process_video(tmp_path, posture_type)
        os.remove(tmp_path)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
