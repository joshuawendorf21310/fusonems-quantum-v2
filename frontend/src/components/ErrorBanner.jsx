import { useEffect, useState } from 'react'
import { subscribeErrors } from '../services/errorBus.js'

export default function ErrorBanner() {
  const [current, setCurrent] = useState(null)

  useEffect(() => {
    return subscribeErrors((payload) => {
      setCurrent(payload)
    })
  }, [])

  if (!current) {
    return null
  }

  return (
    <div className="error-banner" role="alert">
      <div>
        <strong>Action needed:</strong> {current.message}
        {current.status ? <span className="error-code">Code {current.status}</span> : null}
      </div>
      <button className="ghost-button" type="button" onClick={() => setCurrent(null)}>
        Dismiss
      </button>
    </div>
  )
}
