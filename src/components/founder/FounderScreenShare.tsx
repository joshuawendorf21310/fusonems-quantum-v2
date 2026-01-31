import React, { useRef, useState } from "react";

export default function FounderScreenShare() {
  const [sharing, setSharing] = useState(false);
  const [stream, setStream] = useState(null);
  const videoRef = useRef(null);

  const handleShareScreen = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      setStream(mediaStream);
      setSharing(true);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      // TODO: Connect to signaling server (FastAPI backend) and establish WebRTC peer connection
    } catch (err) {
      alert("Screen sharing failed: " + err.message);
    }
  };

  const handleStopSharing = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setSharing(false);
    }
  };

  return (
    <div className="screen-share-panel" style={{ maxWidth: 480, margin: "0 auto", background: "#18181b", borderRadius: 16, boxShadow: "0 4px 24px #0002", padding: 24 }}>
      <h2 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: 12, color: "#fff" }}>Screen Share</h2>
      <div style={{ marginBottom: 16 }}>
        {!sharing ? (
          <button onClick={handleShareScreen} style={{ background: "#3b82f6", color: "#fff", border: "none", borderRadius: 8, padding: "10px 18px", fontWeight: 600, cursor: "pointer" }}>
            Share My Screen
          </button>
        ) : (
          <button onClick={handleStopSharing} style={{ background: "#ef4444", color: "#fff", border: "none", borderRadius: 8, padding: "10px 18px", fontWeight: 600, cursor: "pointer" }}>
            Stop Sharing
          </button>
        )}
      </div>
      <video ref={videoRef} autoPlay playsInline style={{ width: "100%", borderRadius: 8, background: "#23232a" }} />
      <div style={{ marginTop: 18, fontSize: "0.95rem", color: "#a3a3a3" }}>
        <strong>Features coming soon:</strong> Viewer list, permissions, session controls, and real-time peer-to-peer streaming via WebRTC and FastAPI signaling.
      </div>
    </div>
  );
}
