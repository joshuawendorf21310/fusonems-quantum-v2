"use client"

import { useState, useEffect, useRef } from "react"
import { useParams } from "next/navigation"

interface VideoSession {
  id: string
  patientName: string
  appointmentTime: string
  status: string
}

export default function ProviderVideoRoomPage() {
  const params = useParams()
  const sessionId = params.sessionId as string
  
  const [session, setSession] = useState<VideoSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isVideoOff, setIsVideoOff] = useState(false)
  const [chatMessages, setChatMessages] = useState<Array<{ sender: string; message: string; time: string }>>([])
  const [chatInput, setChatInput] = useState("")
  const [showChat, setShowChat] = useState(false)
  
  const localVideoRef = useRef<HTMLVideoElement>(null)
  const remoteVideoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    fetchSessionData()
    initializeVideo()
  }, [sessionId])

  const fetchSessionData = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/carefusion/provider/video/${sessionId}`, {
        credentials: "include"
      })
      
      if (!response.ok) throw new Error("Failed to fetch session data")
      
      const data = await response.json()
      setSession(data.session)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error loading session")
    } finally {
      setLoading(false)
    }
  }

  const initializeVideo = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream
      }
      setIsConnected(true)
    } catch (err) {
      setError("Failed to access camera/microphone. Please check permissions.")
    }
  }

  const toggleMute = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream
      stream.getAudioTracks().forEach(track => {
        track.enabled = !track.enabled
      })
      setIsMuted(!isMuted)
    }
  }

  const toggleVideo = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream
      stream.getVideoTracks().forEach(track => {
        track.enabled = !track.enabled
      })
      setIsVideoOff(!isVideoOff)
    }
  }

  const endCall = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream
      stream.getTracks().forEach(track => track.stop())
    }
    window.close()
  }

  const sendChatMessage = () => {
    if (!chatInput.trim()) return
    
    const newMessage = {
      sender: "Provider",
      message: chatInput,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
    
    setChatMessages([...chatMessages, newMessage])
    setChatInput("")
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400">Connecting to video session...</p>
        </div>
      </div>
    )
  }

  if (error && !session) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-8">
        <div className="max-w-md w-full bg-red-950/50 border border-red-800 text-red-300 px-6 py-4 rounded-lg">
          {error}
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="h-screen flex flex-col">
        <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">{session?.patientName}</h1>
              <p className="text-sm text-zinc-400">
                {isConnected ? "Connected" : "Connecting..."}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-zinc-400">{session?.appointmentTime}</span>
              <span className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500" : "bg-yellow-500"}`}></span>
            </div>
          </div>
        </div>

        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 relative bg-black">
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
            
            {!isConnected && (
              <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
                <div className="text-center">
                  <div className="w-32 h-32 bg-zinc-800 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-4xl font-bold text-zinc-600">
                      {session?.patientName.charAt(0)}
                    </span>
                  </div>
                  <p className="text-zinc-400">Waiting for patient to join...</p>
                </div>
              </div>
            )}

            <div className="absolute bottom-20 right-6 w-64 h-48 bg-zinc-900 border-2 border-zinc-700 rounded-lg overflow-hidden shadow-2xl">
              <video
                ref={localVideoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover"
              />
              {isVideoOff && (
                <div className="absolute inset-0 bg-zinc-900 flex items-center justify-center">
                  <div className="w-16 h-16 bg-zinc-800 rounded-full flex items-center justify-center">
                    <span className="text-2xl font-bold text-zinc-600">You</span>
                  </div>
                </div>
              )}
            </div>

            <div className="absolute bottom-6 left-1/2 transform -translate-x-1/2 flex items-center gap-4 bg-zinc-900/95 px-6 py-4 rounded-full border border-zinc-800">
              <button
                onClick={toggleMute}
                className={`w-12 h-12 rounded-full flex items-center justify-center transition ${
                  isMuted ? "bg-red-600 hover:bg-red-700" : "bg-zinc-700 hover:bg-zinc-600"
                }`}
                title={isMuted ? "Unmute" : "Mute"}
              >
                {isMuted ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                  </svg>
                )}
              </button>

              <button
                onClick={toggleVideo}
                className={`w-12 h-12 rounded-full flex items-center justify-center transition ${
                  isVideoOff ? "bg-red-600 hover:bg-red-700" : "bg-zinc-700 hover:bg-zinc-600"
                }`}
                title={isVideoOff ? "Turn on camera" : "Turn off camera"}
              >
                {isVideoOff ? (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3l18 18" />
                  </svg>
                ) : (
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </button>

              <button
                onClick={() => setShowChat(!showChat)}
                className="w-12 h-12 rounded-full bg-zinc-700 hover:bg-zinc-600 flex items-center justify-center transition"
                title="Chat"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </button>

              <button
                onClick={endCall}
                className="w-12 h-12 rounded-full bg-red-600 hover:bg-red-700 flex items-center justify-center transition"
                title="End call"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {showChat && (
            <div className="w-96 bg-zinc-900 border-l border-zinc-800 flex flex-col">
              <div className="px-6 py-4 border-b border-zinc-800">
                <h2 className="text-lg font-semibold">Chat</h2>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {chatMessages.length === 0 ? (
                  <p className="text-center text-zinc-500 text-sm">No messages yet</p>
                ) : (
                  chatMessages.map((msg, index) => (
                    <div key={index} className="bg-zinc-800 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-sm">{msg.sender}</span>
                        <span className="text-xs text-zinc-500">{msg.time}</span>
                      </div>
                      <p className="text-sm">{msg.message}</p>
                    </div>
                  ))
                )}
              </div>

              <div className="p-4 border-t border-zinc-800">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && sendChatMessage()}
                    placeholder="Type a message..."
                    className="flex-1 px-4 py-2 bg-zinc-950 border border-zinc-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 text-sm"
                  />
                  <button
                    onClick={sendChatMessage}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition"
                  >
                    Send
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
