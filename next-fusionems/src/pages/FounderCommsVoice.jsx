import { useEffect, useMemo, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderCommsVoice() {
  const [threads, setThreads] = useState([])

  useEffect(() => {
    apiFetch('/api/comms/threads').then((data) => {
      setThreads(Array.isArray(data) ? data : [])
    })
  }, [])

  const voiceThreads = useMemo(
    () => threads.filter((thread) => thread.channel === 'voice'),
    [threads]
  )

  const columns = [
    { key: 'subject', label: 'Subject' },
    { key: 'priority', label: 'Priority' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Comms" title="Voice Operations" />
      <div className="panel">
        <DataTable columns={columns} rows={voiceThreads} emptyState="No voice threads." />
      </div>
    </div>
  )
}
