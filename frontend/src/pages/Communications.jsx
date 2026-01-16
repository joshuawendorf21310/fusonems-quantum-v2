import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackCommsCalls, fallbackCommsMessages, fallbackCommsThreads } from '../data/fallback.js'

export default function Communications() {
  const [threads, setThreads] = useState(fallbackCommsThreads)
  const [messages, setMessages] = useState(fallbackCommsMessages)
  const [calls, setCalls] = useState(fallbackCommsCalls)
  const [health, setHealth] = useState({
    status: 'unknown',
    configured: false,
    telnyx_number: null,
  })
  const [timelineId, setTimelineId] = useState(fallbackCommsCalls[0]?.external_call_id || '')
  const [timeline, setTimeline] = useState([])
  const [activeThread, setActiveThread] = useState(fallbackCommsThreads[0]?.id || null)
  const [formState, setFormState] = useState({
    sender: 'Dispatch',
    body: '',
    media_url: '',
  })
  const [status, setStatus] = useState('')

  const threadColumns = [
    { key: 'subject', label: 'Thread' },
    { key: 'channel', label: 'Channel' },
    { key: 'priority', label: 'Priority' },
    { key: 'status', label: 'Status' },
  ]

  const messageColumns = [
    { key: 'sender', label: 'Sender' },
    { key: 'body', label: 'Message' },
    { key: 'delivery_status', label: 'Status' },
  ]

  const callColumns = [
    { key: 'caller', label: 'Caller' },
    { key: 'recipient', label: 'Recipient' },
    { key: 'duration_seconds', label: 'Duration' },
    { key: 'disposition', label: 'Disposition' },
  ]

  const timelineColumns = [
    { key: 'event_type', label: 'Event' },
    { key: 'provider_event_id', label: 'Provider ID' },
    { key: 'occurred_at', label: 'Occurred' },
  ]

  const loadThreads = async () => {
    try {
      const data = await apiFetch('/api/comms/threads')
      if (Array.isArray(data) && data.length > 0) {
        setThreads(data)
        setActiveThread(data[0]?.id || null)
      }
    } catch (error) {
      console.warn('Threads unavailable', error)
    }
  }

  const loadMessages = async (threadId) => {
    if (!threadId) return
    try {
      const data = await apiFetch(`/api/comms/threads/${threadId}/messages`)
      if (Array.isArray(data)) {
        setMessages(data)
      }
    } catch (error) {
      console.warn('Messages unavailable', error)
    }
  }

  const loadCalls = async () => {
    try {
      const data = await apiFetch('/api/comms/calls')
      if (Array.isArray(data) && data.length > 0) {
        setCalls(data)
      }
    } catch (error) {
      console.warn('Call logs unavailable', error)
    }
  }

  const loadHealth = async () => {
    try {
      const data = await apiFetch('/api/comms/health')
      if (data?.status) {
        setHealth(data)
      }
    } catch (error) {
      console.warn('Comms health unavailable', error)
    }
  }

  const loadTimeline = async () => {
    if (!timelineId) {
      setTimeline([])
      return
    }
    try {
      const data = await apiFetch(`/api/comms/calls/${timelineId}/timeline`)
      if (Array.isArray(data)) {
        setTimeline(data)
      }
    } catch (error) {
      console.warn('Timeline unavailable', error)
    }
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setStatus('Sending...')
    try {
      const payload = {
        thread_id: activeThread,
        sender: formState.sender,
        body: formState.body,
      }
      if (formState.media_url) {
        payload.media_url = formState.media_url
      }
      await apiFetch('/api/comms/messages', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      await loadMessages(activeThread)
      setStatus('Sent')
    } catch (error) {
      setStatus('Failed')
      console.warn('Comms send failed', error)
    }
  }

  useEffect(() => {
    loadThreads()
    loadCalls()
    loadHealth()
  }, [])

  useEffect(() => {
    loadMessages(activeThread)
  }, [activeThread])

  useEffect(() => {
    loadTimeline()
  }, [timelineId])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Communications"
        title="Command Inbox + Incident Comms"
        action={<button className="ghost-button">Create Broadcast</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Threads" title="Active Conversations" />
          <DataTable
            columns={threadColumns}
            rows={threads}
            emptyState="No comms threads yet."
          />
          <div className="panel-actions">
            {threads.map((thread) => (
              <button
                key={thread.id}
                className={thread.id === activeThread ? 'primary-button' : 'ghost-button'}
                onClick={() => setActiveThread(thread.id)}
              >
                Focus {thread.subject || `Thread ${thread.id}`}
              </button>
            ))}
          </div>
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="AI Triage"
            model="comms-orchestrator"
            version="1.6"
            level="ADVISORY"
            message="2 threads marked high priority. Suggested escalation to supervisor."
            reason="Sentiment + SLA drift detection"
          />
          <div className="note-card">
            <p className="note-title">Incident Broadcast</p>
            <p className="note-body">One active advisory running for Zone 4 weather hold.</p>
          </div>
          <div className="note-card">
            <p className="note-title">Telnyx Health</p>
            <p className="note-body">
              Status: {health.status} · Configured: {health.configured ? 'Yes' : 'No'}
            </p>
            {health.telnyx_number ? (
              <p className="note-sub">Number: {health.telnyx_number}</p>
            ) : null}
          </div>
        </div>
      </div>

      <div className="panel form-panel">
        <SectionHeader eyebrow="Compose" title="Thread Message" />
        <form className="form-grid" onSubmit={handleSubmit}>
          <div>
            <label>Sender</label>
            <input name="sender" value={formState.sender} onChange={handleChange} />
          </div>
          <div className="full-width">
            <label>Message</label>
            <input
              name="body"
              value={formState.body}
              onChange={handleChange}
              placeholder="Dispatch update or patient notice"
              required
            />
          </div>
          <div className="full-width">
            <label>Media URL (optional)</label>
            <input
              name="media_url"
              value={formState.media_url}
              onChange={handleChange}
              placeholder="https://example.com/fax.pdf"
            />
          </div>
          <div className="full-width align-end">
            <button className="primary-button" type="submit">
              Send
            </button>
          </div>
        </form>
        {status ? <p className="status-text">{status}</p> : null}
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Messages" title="Thread History" />
          <DataTable columns={messageColumns} rows={messages} emptyState="No messages yet." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Calls" title="Voice Logs" />
          <DataTable columns={callColumns} rows={calls} emptyState="No calls logged." />
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Timeline" title="Call Event Timeline" />
        <div className="search-input-row">
          <input
            className="text-input"
            value={timelineId}
            onChange={(event) => setTimelineId(event.target.value)}
            placeholder="Enter external call ID"
          />
          <button className="ghost-button" type="button" onClick={loadTimeline}>
            Load Timeline
          </button>
        </div>
        <DataTable columns={timelineColumns} rows={timeline} emptyState="No call events recorded." />
      </div>
    </div>
  )
}
