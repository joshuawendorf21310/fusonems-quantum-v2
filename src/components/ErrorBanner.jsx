import { useEffect, useState, useRef } from "react"
import PropTypes from "prop-types"
import clsx from "clsx"
import { subscribeErrors } from "../services/errorBus.js"

export default function ErrorBanner() {
  const [current, setCurrent] = useState(null)
  const bannerRef = useRef(null)
  const lastFocusedRef = useRef(null)

  useEffect(() => {
    const unsubscribe = subscribeErrors((payload) => {
      if (!payload || typeof payload.message !== "string") {
        return
      }
      setCurrent(payload)
    })

    return () => {
      if (typeof unsubscribe === "function") unsubscribe()
    }
  }, [])

  useEffect(() => {
    if (current && bannerRef.current) {
      lastFocusedRef.current = document.activeElement
      bannerRef.current.focus()
    }
    return () => {
      if (!current && lastFocusedRef.current instanceof HTMLElement) {
        lastFocusedRef.current.focus()
      }
    }
  }, [current])

  if (!current) return null

  const {
    message,
    status,
    level = "error",
    source,
  } = current

  const levelLabel = String(level).toUpperCase()

  return (
    <section
      ref={bannerRef}
      tabIndex={-1}
      className={clsx("error-banner", `error-banner-${level}`)}
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="error-banner-content">
        <strong className="error-banner-title">
          ACTION REQUIRED
        </strong>

        <span className="error-banner-message">
          {message}
        </span>

        {status && (
          <span className="error-banner-code">
            CODE {status}
          </span>
        )}

        {source && (
          <span className="error-banner-source">
            {source}
          </span>
        )}
      </div>

      <button
        className="ghost-button error-banner-dismiss"
        type="button"
        aria-label="Dismiss error"
        onClick={() => setCurrent(null)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setCurrent(null)
        }}
      >
        Dismiss
      </button>
    </section>
  )
}
