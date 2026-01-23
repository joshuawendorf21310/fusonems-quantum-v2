import { useEffect, useState } from "react"
import PropTypes from "prop-types"
import clsx from "clsx"
import { apiFetch } from "../services/api.js"

export default function LegalHoldBanner({ scopeType, scopeId }) {
  const [holds, setHolds] = useState([])
  const [error, setError] = useState(null)

  const bannerId = `legal-hold-${scopeType || "unknown"}-${scopeId || "unknown"}`
  const messageId = `${bannerId}-message`

  useEffect(() => {
    let mounted = true

    const load = async () => {
      if (!scopeType || !scopeId) {
        setHolds([])
        return
      }
      try {
        const data = await apiFetch(
          `/api/legal-hold?scope_type=${encodeURIComponent(
            scopeType
          )}&scope_id=${encodeURIComponent(scopeId)}`
        )
        if (mounted && Array.isArray(data)) {
          setHolds(data)
          setError(null)
        }
      } catch (err) {
        if (mounted) {
          console.warn("Unable to load legal holds", err)
          setError("Unable to determine legal hold status")
        }
      }
    }

    load()
    return () => {
      mounted = false
    }
  }, [scopeType, scopeId])

  const activeHold = holds.find(
    (hold) => hold && hold.status && hold.status !== "Released"
  )

  if (error) {
    return (
      <section
        id={bannerId}
        className="legal-banner warning"
        role="status"
        aria-live="polite"
        aria-describedby={messageId}
      >
        <p id={messageId}>{error}</p>
      </section>
    )
  }

  if (!activeHold) {
    return (
      <section
        id={bannerId}
        className="legal-banner neutral"
        role="status"
        aria-live="polite"
        aria-describedby={messageId}
      >
        <p id={messageId}>Legal Hold: None</p>
      </section>
    )
  }

  return (
    <section
      id={bannerId}
      className={clsx("legal-banner", "alert")}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      aria-describedby={messageId}
    >
      <p id={messageId}>
        LEGAL HOLD ACTIVE —{" "}
        {activeHold.reason || "Pending legal review"}{" "}
        <span className="legal-banner-meta">
          (initiated by {activeHold.created_by || "compliance"})
        </span>
      </p>
    </section>
  )
}

LegalHoldBanner.propTypes = {
  scopeType: PropTypes.string,
  scopeId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
}
