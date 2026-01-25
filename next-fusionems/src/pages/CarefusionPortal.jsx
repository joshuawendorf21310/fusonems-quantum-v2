import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function CarefusionPortal() {
  const [ledger, setLedger] = useState([])
  const [claims, setClaims] = useState([])

  useEffect(() => {
    const load = async () => {
      const [ledgerData, claimData] = await Promise.all([
        apiFetch('/api/carefusion/ledger'),
        apiFetch('/api/carefusion/claims'),
      ])
      setLedger(Array.isArray(ledgerData) ? ledgerData : [])
      setClaims(Array.isArray(claimData) ? claimData : [])
    }
    load()
  }, [])

  const ledgerColumns = [
    { key: 'entry_type', label: 'Type' },
    { key: 'account', label: 'Account' },
    { key: 'amount', label: 'Amount', render: (row) => `$${(row.amount / 100).toFixed(2)}` },
  ]
  const claimColumns = [
    { key: 'encounter_id', label: 'Encounter' },
    { key: 'payer', label: 'Payer' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader eyebrow="CareFusion" title="Telehealth Billing Portal" />
      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Ledger" title="CareFusion Ledger" />
          <DataTable columns={ledgerColumns} rows={ledger} emptyState="No ledger entries." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Claims" title="Telehealth Claims" />
          <DataTable columns={claimColumns} rows={claims} emptyState="No claims." />
        </div>
      </div>
    </div>
  )
}
