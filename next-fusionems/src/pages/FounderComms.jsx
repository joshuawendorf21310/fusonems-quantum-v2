import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderComms() {
  const [threads, setThreads] = useState([])
  const [queue, setQueue] = useState({ events: [], attempts: [] })

  useEffect(() => {
    const load = async () => {
      const [threadData, queueData] = await Promise.all([
        apiFetch('/api/comms/threads'),
        apiFetch('/api/comms/queue'),
      ])
      setThreads(Array.isArray(threadData) ? threadData : [])
      setQueue(queueData || { events: [], attempts: [] })
    }
    load()
  }, [])

  const threadColumns = [
    { key: 'channel', label: 'Channel' },
    { key: 'subject', label: 'Subject' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]
  const eventColumns = [
    { key: 'event_type', label: 'Event' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Comms" title="Communications Hub" />
      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Threads" title="All Channels" />
          <DataTable columns={threadColumns} rows={threads} emptyState="No comms threads." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Queue" title="Delivery Events" />
          <DataTable columns={eventColumns} rows={queue.events || []} emptyState="No delivery events." />
        </div>
      </div>
    </div>
  )
}
