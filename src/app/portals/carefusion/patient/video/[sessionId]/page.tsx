"use client"

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'

interface VideoSession {
  id: string
  appointmentId: string
  providerName: string
  providerSpecialty: string
  patientName: string
  status: 'waiting' | 'active' | 'ended'
  startTime?: string
  endTime?: string
}

export default function VideoConsultationPage() {
  const router = useRouter()
  const params = useParams()
  const sessionId = params.sessionId as string

  const [session, setSession] = useState<VideoSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isMuted, setIsMuted] = useState(false)
  const [isVideoOff, setIsVideoOff] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')

  const localVideoRef = useRef<HTMLVideoElement>(null)
  const remoteVideoRef = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    if (sessionId) {
      fetchSession()
      initializeMedia()
    }

    return () => {
      // Cleanup media streams
      if (localVideoRef.current && localVideoRef.current.srcObject) {
        const stream = localVideoRef.current.srcObject as MediaStream
        stream.getTracks().forEach(track => track.stop())
      }
    }
  }, [sessionId])

  const fetchSession = async () => {
    try {
      setLoading(true)
      const response = await fetch(`/api/carefusion/patient/video/${sessionId}`, {
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to fetch video session')
      }
      
      const data = await response.json()
      setSession(data.session)
      setConnectionStatus('connected')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
      setConnectionStatus('disconnected')
    } finally {
      setLoading(false)
    }
  }

  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      })

      if (localVideoRef.current) {
        localVideoRef.current.srcObject = stream
      }
    } catch (err) {
      console.error('Error accessing media devices:', err)
      setError('Unable to access camera or microphone. Please check permissions.')
    }
  }

  const toggleMute = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream
      const audioTrack = stream.getAudioTracks()[0]
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled
        setIsMuted(!audioTrack.enabled)
      }
    }
  }

  const toggleVideo = () => {
    if (localVideoRef.current && localVideoRef.current.srcObject) {
      const stream = localVideoRef.current.srcObject as MediaStream
      const videoTrack = stream.getVideoTracks()[0]
      if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled
        setIsVideoOff(!videoTrack.enabled)
      }
    }
  }

  const handleEndCall = async () => {
    if (!confirm('Are you sure you want to end this consultation?')) {
      return
    }

    try {
      const response = await fetch(`/api/carefusion/patient/video/${sessionId}/end`, {
        method: 'POST',
        credentials: 'include'
      })
      
      if (!response.ok) {
        throw new Error('Failed to end session')
      }
      
      router.push('/portals/carefusion/patient/appointments')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to end session')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-cyan-500 mb-4 mx-auto"></div>
          <p className="text-zinc-400 text-lg">Connecting to video session...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-red-900/20 border border-red-800 rounded-lg p-6">
            <h2 className="text-2xl font-bold text-red-400 mb-4">Connection Error</h2>
            <p className="text-red-400 mb-4">{error}</p>
            <button
              onClick={() => router.push('/portals/carefusion/patient/appointments')}
              className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors"
            >
              Return to Appointments
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Header */}
      <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Video Consultation</h1>
            {session && (
              <p className="text-zinc-400 text-sm">
                with {session.providerName} - {session.providerSpecialty}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              connectionStatus === 'connected' ? 'bg-green-600/20 text-green-400' :
              connectionStatus === 'connecting' ? 'bg-yellow-600/20 text-yellow-400' :
              'bg-red-600/20 text-red-400'
            }`}>
              {connectionStatus === 'connected' && '● Connected'}
              {connectionStatus === 'connecting' && '● Connecting...'}
              {connectionStatus === 'disconnected' && '● Disconnected'}
            </div>
          </div>
        </div>
      </div>

      {/* Video Grid */}
      <div className="relative h-[calc(100vh-180px)] p-6">
        <div className="max-w-7xl mx-auto h-full">
          {/* Remote Video (Provider) */}
          <div className="relative w-full h-full bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800">
            <video
              ref={remoteVideoRef}
              autoPlay
              playsInline
              className="w-full h-full object-cover"
            />
            
            {/* Placeholder when provider not connected */}
            <div className="absolute inset-0 flex items-center justify-center bg-zinc-900">
              <div className="text-center">
                <div className="w-32 h-32 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-4xl font-bold mx-auto mb-4">
                  {session?.providerName.split(' ').map(n => n[0]).join('')}
                </div>
                <p className="text-xl font-semibold mb-2">{session?.providerName}</p>
                <p className="text-zinc-400">{session?.providerSpecialty}</p>
                <p className="text-zinc-500 text-sm mt-4">Waiting for provider to join...</p>
              </div>
            </div>

            {/* Local Video (Patient) - Picture-in-Picture */}
            <div className="absolute bottom-6 right-6 w-64 h-48 bg-zinc-800 rounded-lg overflow-hidden border-2 border-zinc-700 shadow-lg">
              <video
                ref={localVideoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-cover mirror"
              />
              {isVideoOff && (
                <div className="absolute inset-0 flex items-center justify-center bg-zinc-800">
                  <div className="text-center">
                    <div className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-xl font-bold mx-auto mb-2">
                      {session?.patientName.split(' ').map(n => n[0]).join('')}
                    </div>
                    <p className="text-sm text-zinc-400">Camera Off</p>
                  </div>
                </div>
              )}
              <div className="absolute top-2 left-2 px-2 py-1 bg-black/50 rounded text-xs">
                You
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="fixed bottom-0 left-0 right-0 bg-zinc-900 border-t border-zinc-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-center gap-4">
          {/* Mute Button */}
          <button
            onClick={toggleMute}
            className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl font-medium transition-all ${
              isMuted
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-zinc-800 hover:bg-zinc-700 text-white'
            }`}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? '🔇' : '🎤'}
          </button>

          {/* Video Toggle Button */}
          <button
            onClick={toggleVideo}
            className={`w-16 h-16 rounded-full flex items-center justify-center text-2xl font-medium transition-all ${
              isVideoOff
                ? 'bg-red-600 hover:bg-red-700 text-white'
                : 'bg-zinc-800 hover:bg-zinc-700 text-white'
            }`}
            title={isVideoOff ? 'Turn On Camera' : 'Turn Off Camera'}
          >
            {isVideoOff ? '📹' : '📹'}
          </button>

          {/* End Call Button */}
          <button
            onClick={handleEndCall}
            className="w-16 h-16 rounded-full bg-red-600 hover:bg-red-700 text-white flex items-center justify-center text-2xl font-medium transition-all"
            title="End Call"
          >
            📞
          </button>

          {/* Settings Button */}
          <button
            className="w-16 h-16 rounded-full bg-zinc-800 hover:bg-zinc-700 text-white flex items-center justify-center text-2xl font-medium transition-all"
            title="Settings"
          >
            ⚙️
          </button>
        </div>
      </div>

      <style jsx>{`
        .mirror {
          transform: scaleX(-1);
        }
      `}</style>
    </div>
  )
}
