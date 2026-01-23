import PropTypes from "prop-types"
import clsx from "clsx"

export default function AdvisoryPanel({
  title,
  model,
  version,
  level = "info",
  message,
  reason,
}) {
  const modelStamp =
    model ? (version ? `${model} v${version}` : model) : "Unknown"

  const levelLabel = String(level).toUpperCase()

  const titleId = `advisory-title-${level}-${title.replace(/\s+/g, "-").toLowerCase()}`
  const messageId = `${titleId}-message`

  return (
    <section
      className={clsx("advisory-panel", `advisory-${level}`)}
      role="status"
      aria-live="polite"
      aria-labelledby={titleId}
      aria-describedby={messageId}
    >
      <header className="advisory-header">
        <h3 id={titleId} className="advisory-title">{title}</h3>
        <span
          className={clsx("advisory-badge", `advisory-badge-${level}`)}
          aria-label={`Advisory level: ${levelLabel}`}
        >
          {levelLabel}
        </span>
      </header>

      <p id={messageId} className="advisory-text">{message}</p>

      <div className="advisory-meta">
        <span className="advisory-meta-item">
          <strong>Model:</strong> {modelStamp}
        </span>
        {reason && (
          <span className="advisory-meta-item">
            <strong>Why:</strong> {reason}
          </span>
        )}
      </div>
    </section>
  )
}

AdvisoryPanel.propTypes = {
  title: PropTypes.string.isRequired,
  model: PropTypes.string,
  version: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  level: PropTypes.oneOf(["info", "warning", "error", "critical"]),
  message: PropTypes.string.isRequired,
  reason: PropTypes.string,
}
