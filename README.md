# Full-Stack Rule-Based Bad Posture Detection App

## Objective

This application allows users to upload a video or use their webcam while performing a **squat** or **sitting at a desk**. The system analyzes the posture using **rule-based logic** and flags instances of **bad posture** such as:
- Slouching
- Knee over toe (for squats)
- Hunched back or bent neck (for sitting)

---

## Live Demo

- 🔗 **Frontend (Vercel)**: [https://bad-posture-detector-nine.vercel.app](https://bad-posture-detector-nine.vercel.app)  
- 🔗 **Backend (Render)**: [https://bad-posture-detector-vxw8.onrender.com](https://bad-posture-detector-vxw8.onrender.com)  
- 🎥 **Demo Video (Google Drive)**: [Click to Watch](https://drive.google.com/drive/folders/1uM7QXdydwaimC0Q0GbJxv0dl9hp8Y12P?usp=sharing)

---

## Tech Stack

### Frontend
- React
- Axios
- React Webcam
- Vite (build tool)
- Deployed on **Vercel**

### Backend
- FastAPI
- MediaPipe (Pose Estimation)
- OpenCV (Frame handling)
- NumPy (Geometry calculations)
- Deployed on **Render**

---

## Rule-Based Logic

### For **Squat**:
- ❌ **Bad Posture** if:
  - Knee goes beyond toe
  - Back angle < 150°

### For **Sitting**:
- ❌ **Bad Posture** if:
  - Neck bend angle > 30°
  - Back not upright

---

## 🧪 Features

- Upload a video or use live webcam
- Preview video before upload
- Dark & Light theme toggle
- Real-time posture evaluation
- Frame-by-frame bad posture summary
- Responsive and modern UI

---

## Setup Instructions (Run Locally)

### Prerequisites:
- Python 3.8+
- Node.js 16+
- npm or yarn

### Clone the Repo
```bash
git clone https://github.com/shaik1arif/bad-posture-detector.git
cd bad-posture-detector
```

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
bad-posture-detector/
│
├── backend/
│   └── main.py            # FastAPI backend with rule logic
│
├── frontend/
│   ├── src/
│   │   └── App.jsx        # React main component
│   └── package.json       # Vite + React setup
│
├── README.md
└── ...
```

---

## Submission

- GitHub Repo: [https://github.com/shaik1arif/bad-posture-detector](https://github.com/shaik1arif/bad-posture-detector)
- Frontend: [https://bad-posture-detector-nine.vercel.app](https://bad-posture-detector-nine.vercel.app)
- Backend: [https://bad-posture-detector-vxw8.onrender.com](https://bad-posture-detector-vxw8.onrender.com)
- Demo Video: [Google Drive Link](https://drive.google.com/drive/folders/1uM7QXdydwaimC0Q0GbJxv0dl9hp8Y12P?usp=sharing)

---

## Thank You!

Submitted by Arif Shaik for the Realfy Internship Assignment
