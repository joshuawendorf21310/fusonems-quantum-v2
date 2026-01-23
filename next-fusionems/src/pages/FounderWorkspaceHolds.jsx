import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackLegalCases } from '../data/fallback.js'

const holdColumns = [
  { key: 'id', label: 'Hold' },
  { key: 'scope_type', label: 'Scope' },
  { key: 'scope_id', label: 'Target' },
  { key: 'status', label: 'Status' },
]

export default function FounderWorkspaceHolds() {
  const [holds, setHolds] = useState([])

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch('/api/legal-hold')
        if (Array.isArray(data) && data.length > 0) {
          setHolds(data)
          return
        }
      } catch (error) {
        // fallback below
      }
      setHolds(
        fallbackLegalCases.map((item) => ({
          id: item.id,
          scope_type: 'document_file',
          scope_id: item.case_number,
          status: 'Active',
        }))
      )
    }
    load()
  }, [])

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Workspace" title="Global Holds" />
      <div className="panel">
        <DataTable columns={holdColumns} rows={holds} emptyState="No active holds." />
      </div>
    </div>
  )
}
