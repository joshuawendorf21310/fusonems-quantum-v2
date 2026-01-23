import { useEffect, useState } from 'react'
import { apiFetch } from '../services/api.js'

export default function LegalHoldBanner({ scopeType, scopeId }) {
  const [holds, setHolds] = useState([])

  useEffect(() => {
    const load = async () => {
      if (!scopeType || !scopeId) {
        return
      }
      try {
        const data = await apiFetch(
          `/api/legal-hold?scope_type=${encodeURIComponent(scopeType)}&scope_id=${encodeURIComponent(
            scopeId
          )}`
        )
        if (Array.isArray(data)) {
          setHolds(data)
        }
      } catch (error) {
        console.warn('Unable to load legal holds', error)
      }
    }
    load()
  }, [scopeType, scopeId])

  const activeHold = holds.find((hold) => hold.status !== 'Released')
  if (!activeHold) {
    return (
      <div className="legal-banner neutral">
        <p>Legal Hold: None</p>
      </div>
    )
  }
  return (
    <div className="legal-banner alert">
      <p>
        Legal Hold Active — {activeHold.reason || 'Pending legal review'} (by{' '}
        {activeHold.created_by || 'compliance'})
      </p>
    </div>
  )
}
