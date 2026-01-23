import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackRetentionPolicies } from '../data/fallback.js'

const columns = [
  { key: 'name', label: 'Policy' },
  { key: 'applies_to', label: 'Applies To' },
  { key: 'retention_days', label: 'Days' },
]

export default function RetentionGovernance() {
  const [policies, setPolicies] = useState(fallbackRetentionPolicies)

  useEffect(() => {
    const load = async () => {
      try {
        const data = await apiFetch('/api/founder-ops/governance')
        if (Array.isArray(data) && data.length > 0) {
          setPolicies(data)
        }
      } catch (error) {
        // fallback remains
      }
    }
    load()
  }, [])

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Governance" title="Retention Policies" />
      <div className="panel">
        <AdvisoryPanel
          title="Retention Guardrails"
          model="policy-keeper"
          version="1.0"
          level="ADVISORY"
          message="Policies apply per classification and block deletion while active."
          reason="Vault enforcement"
        />
      </div>
      <div className="panel">
        <DataTable columns={columns} rows={policies} emptyState="No retention policies." />
      </div>
    </div>
  )
}
