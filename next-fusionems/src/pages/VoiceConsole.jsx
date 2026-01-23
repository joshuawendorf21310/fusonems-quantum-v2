import { useEffect, useMemo, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackCommsCalls } from '../data/fallback.js'

export default function VoiceConsole() {
  const [calls, setCalls] = useState(fallbackCommsCalls)
  const [selectedId, setSelectedId] = useState(fallbackCommsCalls[0]?.id || null)
  const [dialNumber, setDialNumber] = useState('')
  const [dialing, setDialing] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch('/api/comms/calls')
        if (Array.isArray(data) && data.length > 0) {
          setCalls(data)
          setSelectedId(data[0]?.id || null)
        }
      } catch (error) {
        // fallback keeps the console alive
      }
    }
    load()
  }, [])

  const selectedCall = useMemo(
    () => calls.find((call) => call.id === selectedId) || calls[0],
    [calls, selectedId]
  )

  const callColumns = [
    { key: 'caller', label: 'From' },
    { key: 'recipient', label: 'To' },
    { key: 'direction', label: 'Dir' },
    { key: 'duration_seconds', label: 'Seconds' },
  ]

  const handleDial = async () => {
    if (!dialNumber) {
      return
    }
    setDialing(true)
    try {
      const payload = {
        caller: 'Dispatch',
        recipient: dialNumber,
        direction: 'outbound',
      }
      const created = await apiFetch('/api/comms/calls/outbound', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      if (created?.id) {
        setCalls((prev) => [created, ...prev])
        setSelectedId(created.id)
      }
    } catch (error) {
      // errors handled globally
    } finally {
      setDialing(false)
    }
  }

  return (
    <div className="page">
      <SectionHeader eyebrow="Quantum Voice" title="Softphone + Call Vault" />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Call History" title="Inbound + Outbound" />
          <DataTable columns={callColumns} rows={calls} emptyState="No calls logged yet." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Live Status" title="Receiving Calls" />
          <AdvisoryPanel
            title="Live Queue"
            model="voice-ops"
            version="1.0"
            level="ADVISORY"
            message="Softphone ready. Connect a routing policy to receive inbound calls."
            reason="Voice routing setup"
          />
          <div className="note-card">
            <p className="note-title">Selected Call</p>
            <p className="note-body">
              {selectedCall
                ? `${selectedCall.caller || 'Unknown'} → ${selectedCall.recipient || 'Unknown'}`
                : 'No active selection.'}
            </p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Dial" title="Outbound Call" />
        <div className="search-input-row">
          <input
            className="text-input"
            placeholder="+1 555-555-0101"
            value={dialNumber}
            onChange={(event) => setDialNumber(event.target.value)}
          />
          <button className="primary-button" onClick={handleDial} disabled={dialing}>
            {dialing ? 'Dialing…' : 'Dial'}
          </button>
        </div>
      </div>
    </div>
  )
}
