import React, { useState, useRef } from 'react';
import axios from 'axios';
import Webcam from 'react-webcam';

const spinnerStyle = {
  border: "6px solid #f3f3f3",
  borderTop: "6px solid #3498db",
  borderRadius: "50%",
  width: "40px",
  height: "40px",
  animation: "spin 1s linear infinite",
  margin: "20px auto",
};

const spinnerKeyframes = `
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
`;

function App() {
  const [video, setVideo] = useState(null);
  const [videoURL, setVideoURL] = useState(null);
  const [postureType, setPostureType] = useState("");
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [useWebcam, setUseWebcam] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [recording, setRecording] = useState(false);
  const [darkMode, setDarkMode] = useState(false);

  const webcamRef = useRef(null);
  const mediaRecorderRef = useRef(null);

  const handleVideoChange = (e) => {
    const file = e.target.files[0];
    setVideo(file);
    setVideoURL(URL.createObjectURL(file));
    setResponse(null);
  };

  const startRecording = () => {
    setRecording(true);
    const stream = webcamRef.current.stream;
    const chunks = [];
    mediaRecorderRef.current = new MediaRecorder(stream, { mimeType: "video/webm" });

    mediaRecorderRef.current.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(chunks, { type: "video/webm" });
      setRecordedBlob(blob);
      setVideoURL(URL.createObjectURL(blob));
    };

    mediaRecorderRef.current.start();
  };

  const stopRecording = () => {
    setRecording(false);
    mediaRecorderRef.current.stop();
  };

  const handleUpload = async () => {
    if ((!video && !recordedBlob) || !postureType) {
      alert("Please select a video or record one, and choose a posture type.");
      return;
    }

    const formData = new FormData();
    const fileToUpload = useWebcam ? recordedBlob : video;
    formData.append("file", fileToUpload, useWebcam ? "webcam_video.webm" : video.name);
    formData.append("posture_type", postureType);

    setLoading(true);
    try {
      const res = await axios.post("https://bad-posture-detector-vxw8.onrender.com/upload-video", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResponse(res.data);
    } catch (err) {
      alert("Upload failed");
      console.error("Upload error:", err.response?.data || err.message);
    }
    setLoading(false);
  };

  return (
    <div style={{
      padding: '2rem',
      fontFamily: 'Arial, sans-serif',
      backgroundColor: darkMode ? '#121212' : '#f0f2f5',
      color: darkMode ? '#f9f9f9' : '#000',
      minHeight: '100vh'
    }}>
      <style>{spinnerKeyframes}</style>

      <h1 style={{
        marginBottom: '1rem',
        color: darkMode ? '#00cfff' : '#007bff',
        textAlign: 'center'
      }}>🧍‍♂️ Bad Posture Detection App</h1>

      <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
        <label>
          <input
            type="checkbox"
            checked={useWebcam}
            onChange={() => {
              setUseWebcam(!useWebcam);
              setVideo(null);
              setRecordedBlob(null);
              setVideoURL(null);
              setResponse(null);
            }}
          /> Use Webcam
        </label>
      </div>

      <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
        <label>
          Select Posture Type:&nbsp;
          <select value={postureType} onChange={(e) => setPostureType(e.target.value)}>
            <option value="">-- Choose --</option>
            <option value="squat">Squat</option>
            <option value="sitting">Sitting</option>
          </select>
        </label>
      </div>

      <div style={{ textAlign: 'center' }}>
        {useWebcam ? (
          <>
            <Webcam ref={webcamRef} width={300} height={225} />
            <div style={{ marginTop: '1rem' }}>
              {!recording ? (
                <button onClick={startRecording}>Start Recording</button>
              ) : (
                <button onClick={stopRecording}>Stop Recording</button>
              )}
            </div>
          </>
        ) : (
          <input type="file" accept="video/*" onChange={handleVideoChange} />
        )}

        {videoURL && (
          <div style={{ marginTop: '1rem' }}>
            <video width="300" controls src={videoURL}></video>
          </div>
        )}
      </div>

      <div style={{
        marginTop: '1.5rem',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '1rem',
        flexWrap: 'wrap'
      }}>
        <button onClick={handleUpload} disabled={loading}>
          Upload & Analyze
        </button>

        <button
          onClick={() => setDarkMode(!darkMode)}
          style={{
            padding: '8px 16px',
            borderRadius: '8px',
            backgroundColor: darkMode ? '#444' : '#ddd',
            color: darkMode ? '#fff' : '#000',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
        </button>
      </div>

      {loading && <div style={spinnerStyle}></div>}

      {response && (
        <div style={{
          marginTop: '2rem',
          padding: '2rem',
          borderRadius: '16px',
          backgroundColor: darkMode ? '#1f1f1f' : '#ffffff',
          color: darkMode ? '#f0f0f0' : '#000',
          boxShadow: '0 6px 20px rgba(0, 0, 0, 0.1)',
          maxWidth: '600px',
          marginLeft: 'auto',
          marginRight: 'auto'
        }}>
          <h2 style={{ color: '#28a745', marginBottom: '1rem' }}>📊 Analysis Result</h2>
          <p><strong>Total Frames:</strong> {response.total_checked_frames}</p>
          <p><strong>Bad Posture Frames:</strong> {response.bad_posture_frames?.length || 0}</p>

          <details style={{ marginTop: '1rem' }}>
            <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>
              Show all flagged frames
            </summary>
            <ul style={{ marginTop: '1rem' }}>
              {(response.bad_posture_frames || []).map((item, idx) => (
                <li key={idx}>
                  <strong>Frame {item.frame}</strong> — 
                  Back Angle: {item.back_angle !== undefined ? item.back_angle.toFixed(1) : 'N/A'}°, 
                  Knee-Toe Diff: {item.knee_toe_diff !== undefined ? item.knee_toe_diff.toFixed(2) : 'N/A'}
                </li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}

export default App;
