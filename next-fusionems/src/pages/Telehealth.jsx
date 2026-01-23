import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import { apiFetch } from '../services/api.js'

export default function Telehealth() {
  const [sessions, setSessions] = useState([])
  const [formState, setFormState] = useState({ title: '', host_name: '' })
  const [selectedSession, setSelectedSession] = useState('')
  const [messages, setMessages] = useState([])
  const [chatState, setChatState] = useState({ sender: '', message: '' })
  const [webrtcConfig, setWebrtcConfig] = useState(null)
  const [secureToken, setSecureToken] = useState(null)

  const loadSessions = async () => {
    try {
      const data = await apiFetch('/api/telehealth/sessions')
      setSessions(data)
      if (!selectedSession && data.length) {
        setSelectedSession(data[0].session_uuid)
      }
    } catch (error) {
      console.warn('Unable to load telehealth sessions', error)
    }
  }

  useEffect(() => {
    loadSessions()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleChatChange = (event) => {
    const { name, value } = event.target
    setChatState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/telehealth/sessions', {
        method: 'POST',
        body: JSON.stringify(formState),
      })
      setFormState({ title: '', host_name: '' })
      await loadSessions()
    } catch (error) {
      console.warn('Unable to create session', error)
    }
  }

  const loadMessages = async (sessionUuid) => {
    if (!sessionUuid) return
    try {
      const data = await apiFetch(`/api/telehealth/sessions/${sessionUuid}/messages`)
      setMessages(data)
    } catch (error) {
      console.warn('Unable to load messages', error)
    }
  }

  const sendMessage = async (event) => {
    event.preventDefault()
    if (!selectedSession) return
    try {
      await apiFetch(`/api/telehealth/sessions/${selectedSession}/messages`, {
        method: 'POST',
        body: JSON.stringify(chatState),
      })
      setChatState({ sender: '', message: '' })
      await loadMessages(selectedSession)
    } catch (error) {
      console.warn('Unable to send message', error)
    }
  }

  const fetchWebrtcConfig = async () => {
    if (!selectedSession) return
    try {
      const data = await apiFetch(`/api/telehealth/sessions/${selectedSession}/webrtc`)
      setWebrtcConfig(data)
    } catch (error) {
      console.warn('Unable to load WebRTC config', error)
    }
  }

  const fetchSecureToken = async () => {
    if (!selectedSession) return
    try {
      const data = await apiFetch(`/api/telehealth/sessions/${selectedSession}/secure-token`)
      setSecureToken(data)
    } catch (error) {
      console.warn('Unable to load secure token', error)
    }
  }

  const captureConsent = async () => {
    if (!selectedSession) return
    try {
      await apiFetch(`/api/telehealth/sessions/${selectedSession}/consent`, {
        method: 'POST',
        body: '{}',
      })
      await loadSessions()
    } catch (error) {
      console.warn('Unable to capture consent', error)
    }
  }

  useEffect(() => {
    loadMessages(selectedSession)
  }, [selectedSession])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Telehealth Video"
        title="CareFusion Telemed Sessions"
        action={<button className="ghost-button">Launch Video Room</button>}
      />

      <div className="section-grid">
        <div className="panel form-panel">
          <form className="form-grid" onSubmit={handleSubmit}>
            <div>
              <label>Session Title</label>
              <input
                name="title"
                value={formState.title}
                onChange={handleChange}
                placeholder="Post-dispatch telehealth"
                required
              />
            </div>
            <div>
              <label>Host Name</label>
              <input
                name="host_name"
                value={formState.host_name}
                onChange={handleChange}
                placeholder="Dr. Skylar"
                required
              />
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Create Session
              </button>
            </div>
          </form>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Live Rooms" title="Active Telehealth Sessions" />
          <div className="stack">
            {sessions.map((session) => (
              <div className="list-row" key={session.session_uuid}>
                <div>
                  <p className="list-title">{session.title}</p>
                  <p className="list-sub">
                    Host: {session.host_name} · Modality: {session.modality}
                  </p>
                  <p className="list-sub">
                    Consent: {session.consent_captured_at ? 'Captured' : 'Required'}
                  </p>
                </div>
                <span className="badge active">{session.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader
            eyebrow="Video Lab"
            title="Secure WebRTC Room"
            action={
              <button className="ghost-button" onClick={fetchWebrtcConfig} type="button">
                Load Room Config
              </button>
            }
          />
          <div className="stack">
            <label>Session</label>
            <select
              value={selectedSession}
              onChange={(event) => setSelectedSession(event.target.value)}
            >
              {sessions.map((session) => (
                <option key={session.session_uuid} value={session.session_uuid}>
                  {session.title}
                </option>
              ))}
            </select>
            <div className="inline-actions">
              <button className="ghost-button" type="button" onClick={captureConsent}>
                Capture Consent
              </button>
              <button className="ghost-button" type="button" onClick={fetchSecureToken}>
                Get Secure Token
              </button>
            </div>
            {webrtcConfig ? (
              <pre className="code-block">{JSON.stringify(webrtcConfig, null, 2)}</pre>
            ) : (
              <p className="hero-text">
                Multi-party video, screen sharing, and secure session logging are
                enabled for CareFusion Telemed. This build uses internal WebRTC
                with no external API keys required.
              </p>
            )}
            {secureToken ? (
              <pre className="code-block">{JSON.stringify(secureToken, null, 2)}</pre>
            ) : null}
          </div>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Chat" title="Telehealth Messaging" />
          <form className="stack" onSubmit={sendMessage}>
            <input
              name="sender"
              value={chatState.sender}
              onChange={handleChatChange}
              placeholder="Sender name"
              required
            />
            <input
              name="message"
              value={chatState.message}
              onChange={handleChatChange}
              placeholder="Message"
              required
            />
            <button className="primary-button" type="submit">
              Send Message
            </button>
          </form>
          <div className="stack">
            {messages.map((message) => (
              <div className="list-row" key={message.id}>
                <div>
                  <p className="list-title">{message.sender}</p>
                  <p className="list-sub">{message.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
