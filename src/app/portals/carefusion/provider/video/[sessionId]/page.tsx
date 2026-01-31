"use client"

import { useState, useEffect, useRef } from "react"
import { useParams, useRouter } from "next/navigation"

interface JitsiEventMap {
  videoConferenceJoined: () => void
  videoConferenceLeft: () => void
  readyToClose: () => void
  errorOccurred: (event: { error?: string; message?: string }) => void
  recordingStatusChanged: (event: { on: boolean; mode?: string }) => void
}

interface JitsiMeetExternalAPI {
  addEventListener<K extends keyof JitsiEventMap>(
    event: K,
    handler: JitsiEventMap[K]
  ): void
  removeEventListener<K extends keyof JitsiEventMap>(
    event: K,
    handler: JitsiEventMap[K]
  ): void
  executeCommand(command: string, ...args: unknown[]): void
  dispose(): void
}

interface JitsiConfigOptions {
  roomName: string
  jwt?: string
  parentNode: HTMLElement
  configOverwrite?: Record<string, unknown>
  interfaceConfigOverwrite?: Record<string, unknown>
  userInfo?: {
    displayName: string
    email?: string
  }
}

declare global {
  interface Window {
    JitsiMeetExternalAPI: new (domain: string, options: JitsiConfigOptions) => JitsiMeetExternalAPI
  }
}

interface JitsiConfig {
  domain: string
  roomName: string
  jwt_token: string
  configOverwrite: Record<string, unknown>
  interfaceConfigOverwrite: Record<string, unknown>
  userInfo: {
    displayName: string
    email?: string
  }
}

export default function ProviderVideoRoomPage() {
  const params = useParams()
  const router = useRouter()
  const sessionId = (params?.sessionId as string) ?? ""
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [joined, setJoined] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')
  const [patientInfo, setPatientInfo] = useState<{ name: string; appointmentTime?: string } | null>(null)
  const [isRecording, setIsRecording] = useState(false)

  const jitsiContainerRef = useRef<HTMLDivElement>(null)
  const jitsiApiRef = useRef<JitsiMeetExternalAPI | null>(null)
  const eventHandlersRef = useRef<Array<{ event: keyof JitsiEventMap; handler: (...args: unknown[]) => void }>>([])

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

      // Start session (provider initiates)
      const startResponse = await fetch(`/api/carefusion/video/room/${sessionId}/start`, {
        method: 'POST',
        credentials: 'include'
      })

      if (!startResponse.ok) {
        throw new Error('Failed to start video session')
      }

      // Fetch room config
      const response = await fetch(`/api/carefusion/video/room/${sessionId}`, {
        credentials: 'include'
      })

      if (!response.ok) {
        throw new Error('Failed to fetch video session configuration')
      }

      const data = await response.json()
      const { jwt_token, jitsi_config, patient_name, appointment_time } = data

      // Store patient info
      setPatientInfo({
        name: patient_name || 'Patient',
        appointmentTime: appointment_time
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
          moderatedRoomServiceUrl: true,
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
            'recording',
            'settings',
            'videoquality',
            'filmstrip',
            'stats',
            'tileview',
            'mute-everyone'
          ],
          ...jitsi_config.interfaceConfigOverwrite
        },
        userInfo: {
          displayName: jitsi_config.userInfo?.displayName || 'Provider',
          email: jitsi_config.userInfo?.email
        }
      })

      // Event listeners with cleanup tracking
      const handleVideoConferenceJoined = () => {
        setJoined(true)
        setConnectionStatus('connected')
        setLoading(false)
      }

      const handleVideoConferenceLeft = () => {
        handleLeave()
      }

      const handleReadyToClose = () => {
        handleLeave()
      }

      const handleErrorOccurred: JitsiEventMap['errorOccurred'] = (event) => {
        console.error('Jitsi error:', event)
        setError(event.message || 'A video conferencing error occurred. Please try rejoining.')
        setConnectionStatus('disconnected')
      }

      const handleRecordingStatusChanged: JitsiEventMap['recordingStatusChanged'] = (event) => {
        setIsRecording(event.on)
      }

      api.addEventListener('videoConferenceJoined', handleVideoConferenceJoined)
      api.addEventListener('videoConferenceLeft', handleVideoConferenceLeft)
      api.addEventListener('readyToClose', handleReadyToClose)
      api.addEventListener('errorOccurred', handleErrorOccurred)
      api.addEventListener('recordingStatusChanged', handleRecordingStatusChanged)

      // Store handlers for cleanup
      eventHandlersRef.current = [
        { event: 'videoConferenceJoined', handler: handleVideoConferenceJoined },
        { event: 'videoConferenceLeft', handler: handleVideoConferenceLeft },
        { event: 'readyToClose', handler: handleReadyToClose },
        { event: 'errorOccurred', handler: handleErrorOccurred },
        { event: 'recordingStatusChanged', handler: handleRecordingStatusChanged },
      ]

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
    router.push('/portals/carefusion/provider/appointments')
  }

  const handleEndSession = async () => {
    if (!confirm('Are you sure you want to end this session? This will disconnect all participants.')) {
      return
    }

    try {
      // Notify backend to end session
      await fetch(`/api/carefusion/video/room/${sessionId}/end`, {
        method: 'POST',
        credentials: 'include'
      })
    } catch (err) {
      console.error('Error ending session:', err)
    }

    handleLeave()
  }

  const toggleRecording = () => {
    if (jitsiApiRef.current) {
      if (isRecording) {
        jitsiApiRef.current.executeCommand('stopRecording', 'file')
      } else {
        jitsiApiRef.current.executeCommand('startRecording', {
          mode: 'file'
        })
      }
    }
  }

  const muteAllParticipants = () => {
    if (jitsiApiRef.current) {
      jitsiApiRef.current.executeCommand('muteEveryone')
    }
  }

  const cleanup = () => {
    if (jitsiApiRef.current) {
      // Remove all event listeners before disposing
      eventHandlersRef.current.forEach(({ event, handler }) => {
        try {
          jitsiApiRef.current?.removeEventListener(event, handler)
        } catch (err) {
          console.warn(`Failed to remove event listener for ${event}:`, err)
        }
      })
      eventHandlersRef.current = []
      
      jitsiApiRef.current.dispose()
      jitsiApiRef.current = null
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-zinc-400 text-lg">Connecting to video session...</p>
          <p className="text-zinc-500 text-sm mt-2">Please wait while we prepare the consultation room</p>
        </div>
      </div>
    )
  }

  if (error && !jitsiApiRef.current) {
    return (
      <div className="min-h-screen bg-zinc-950 text-zinc-100 flex items-center justify-center p-8">
        <div className="max-w-md w-full">
          <div className="bg-red-950/50 border border-red-800 text-red-300 px-6 py-4 rounded-lg mb-4">
            <h2 className="text-xl font-bold mb-2">Connection Error</h2>
            <p>{error}</p>
          </div>
          <div className="flex gap-4">
            <button
              onClick={() => {
                setError(null)
                setLoading(true)
                loadJitsiScript()
              }}
              className="flex-1 px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => router.push('/portals/carefusion/provider/appointments')}
              className="flex-1 px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors"
            >
              Back to Appointments
            </button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Provider Header with Controls */}
      <div className="bg-zinc-900 border-b border-zinc-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">
              {patientInfo ? `Video Consultation with ${patientInfo.name}` : 'Video Consultation'}
            </h1>
            {patientInfo?.appointmentTime && (
              <p className="text-sm text-zinc-400">
                Scheduled: {patientInfo.appointmentTime}
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            {/* Connection Status */}
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

            {/* Recording Indicator */}
            {isRecording && (
              <div className="px-3 py-1 rounded-full text-sm font-medium bg-red-600/20 text-red-400 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full animate-pulse bg-red-500"></span>
                Recording
              </div>
            )}

            {/* Moderator Controls */}
            <button
              onClick={toggleRecording}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors text-sm"
              title={isRecording ? 'Stop Recording' : 'Start Recording'}
            >
              {isRecording ? 'Stop Recording' : 'Record'}
            </button>

            <button
              onClick={muteAllParticipants}
              className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg font-medium transition-colors text-sm"
              title="Mute All Participants"
            >
              Mute All
            </button>

            {/* End Session Button */}
            <button
              onClick={handleEndSession}
              className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors text-sm"
            >
              End Session
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
