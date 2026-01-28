"use client"

import { useState, useEffect, useRef } from 'react'
import { useRouter, useParams } from 'next/navigation'

declare global {
  interface Window {
    JitsiMeetExternalAPI: any
  }
}

interface JitsiConfig {
  domain: string
  roomName: string
  jwt_token: string
  configOverwrite: Record<string, any>
  interfaceConfigOverwrite: Record<string, any>
  userInfo: {
    displayName: string
    email?: string
  }
}

export default function VideoConsultationPage() {
  const router = useRouter()
  const params = useParams()
  const sessionId = params.sessionId as string

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [joined, setJoined] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [providerInfo, setProviderInfo] = useState<{ name: string; specialty: string } | null>(null)

  const jitsiContainerRef = useRef<HTMLDivElement>(null)
  const jitsiApiRef = useRef<any>(null)

  useEffect(() => {
    loadJitsiScript()

    return () => {
      cleanup()
    }
  }, [sessionId])

  const loadJitsiScript = () => {
    // Check if script already loaded
    if (window.JitsiMeetExternalAPI) {
      initializeJitsi()
      return
    }

    const script = document.createElement('script')
    script.src = 'https://jitsi.fusionems.com/external_api.js'
    script.async = true
    script.onload = () => initializeJitsi()
    script.onerror = () => {
      setError('Failed to load video conferencing library. Please check your connection.')
      setLoading(false)
      setConnectionStatus('disconnected')
    }
    document.body.appendChild(script)
  }

  const initializeJitsi = async () => {
    try {
      setLoading(true)
      setConnectionStatus('connecting')

      // Fetch room config from backend
      const response = await fetch(`/api/carefusion/video/room/${sessionId}`, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to fetch video session configuration')
      }

      const data = await response.json()
      const { jwt_token, jitsi_config, provider_name, provider_specialty } = data

      // Store provider info
      setProviderInfo({
        name: provider_name || 'Provider',
        specialty: provider_specialty || 'Healthcare Provider'
      })

      // Initialize Jitsi Meet API
      if (!jitsiContainerRef.current) {
        throw new Error('Video container not ready')
      }

      const domain = jitsi_config.domain || 'jitsi.fusionems.com'
      const roomName = jitsi_config.roomName

      const api = new window.JitsiMeetExternalAPI(domain, {
        roomName: roomName,
        jwt: jwt_token,
        parentNode: jitsiContainerRef.current,
        configOverwrite: {
          startWithAudioMuted: false,
          startWithVideoMuted: false,
          enableWelcomePage: false,
          prejoinPageEnabled: false,
          disableDeepLinking: true,
          ...jitsi_config.configOverwrite
        },
        interfaceConfigOverwrite: {
          SHOW_JITSI_WATERMARK: false,
          SHOW_WATERMARK_FOR_GUESTS: false,
          DEFAULT_BACKGROUND: '#18181b',
          TOOLBAR_BUTTONS: [
            'microphone',
            'camera',
            'closedcaptions',
            'desktop',
            'fullscreen',
            'fodeviceselection',
            'hangup',
            'chat',
            'settings',
            'videoquality',
            'filmstrip',
            'tileview'
          ],
          ...jitsi_config.interfaceConfigOverwrite
        },
        userInfo: {
          displayName: jitsi_config.userInfo?.displayName || 'Patient',
          email: jitsi_config.userInfo?.email
        }
      })

      // Event listeners
      api.addEventListener('videoConferenceJoined', () => {
        setJoined(true)
        setConnectionStatus('connected')
        setLoading(false)
      })

      api.addEventListener('videoConferenceLeft', () => {
        handleLeave()
      })

      api.addEventListener('readyToClose', () => {
        handleLeave()
      })

      api.addEventListener('errorOccurred', (event: any) => {
        console.error('Jitsi error:', event)
        setError('A video conferencing error occurred. Please try rejoining.')
        setConnectionStatus('disconnected')
      })

      jitsiApiRef.current = api
      setLoading(false)

    } catch (err) {
      console.error('Error initializing Jitsi:', err)
      setError(err instanceof Error ? err.message : 'Failed to initialize video session')
      setLoading(false)
      setConnectionStatus('disconnected')
    }
  }

  const handleLeave = () => {
    cleanup()
    router.push('/portals/carefusion/patient/appointments')
  }

  const handleLeaveCall = async () => {
    if (!confirm('Are you sure you want to leave this consultation?')) {
      return
    }

    try {
      // Notify backend
      await fetch(`/api/carefusion/video/room/${sessionId}/leave`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch (err) {
      console.error('Error notifying server of call end:', err)
    }

    handleLeave()
  }

  const cleanup = () => {
    if (jitsiApiRef.current) {
      jitsiApiRef.current.dispose()
      jitsiApiRef.current = null
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-cyan-500 mb-4 mx-auto"></div>
          <p className="text-zinc-400 text-lg">Connecting to video session...</p>
          <p className="text-zinc-500 text-sm mt-2">Please wait while we prepare your consultation</p>
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
            <div className="flex gap-4">
              <button
                onClick={() => {
                  setError(null)
                  setLoading(true)
                  loadJitsiScript()
                }}
                className="px-6 py-3 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg font-medium transition-colors"
              >
                Try Again
              </button>
              <button
                onClick={() => router.push('/portals/carefusion/patient/appointments')}
                className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors"
              >
                Return to Appointments
              </button>
            </div>
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
            {providerInfo && (
              <p className="text-zinc-400 text-sm">
                with {providerInfo.name} - {providerInfo.specialty}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <div className={`px-3 py-1 rounded-full text-sm font-medium flex items-center gap-2 ${
              connectionStatus === 'connected' ? 'bg-green-600/20 text-green-400' :
              connectionStatus === 'connecting' ? 'bg-yellow-600/20 text-yellow-400' :
              'bg-red-600/20 text-red-400'
            }`}>
              <span className="w-2 h-2 rounded-full animate-pulse bg-current"></span>
              {connectionStatus === 'connected' && 'Connected'}
              {connectionStatus === 'connecting' && 'Connecting...'}
              {connectionStatus === 'disconnected' && 'Disconnected'}
            </div>
            <button
              onClick={handleLeaveCall}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors text-sm"
            >
              Leave Call
            </button>
          </div>
        </div>
      </div>

      {/* Jitsi Video Container */}
      <div className="h-[calc(100vh-80px)]">
        <div 
          id="jitsi-meet-container" 
          ref={jitsiContainerRef}
          className="w-full h-full bg-zinc-900"
        />
      </div>

      <style jsx global>{`
        #jitsi-meet-container iframe {
          width: 100%;
          height: 100%;
          border: none;
        }
      `}</style>
    </div>
  )
}
