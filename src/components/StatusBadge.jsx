import PropTypes from "prop-types"
import clsx from "clsx"

const PALETTE = {
  Critical: "badge critical",
  High: "badge high",
  Routine: "badge routine",
  Dispatched: "badge active",
  "En Route": "badge active",
  "On Scene": "badge focus",
  Cleared: "badge muted",
  Queued: "badge muted",
  Scheduled: "badge muted",
  Swapped: "badge focus",
  Available: "badge active",
  Open: "badge high",
  Pending: "badge routine",
}

export default function StatusBadge({ value }) {
  const label =
    typeof value === "string" && value.trim().length > 0
      ? value
      : "Unknown"

  const className = clsx(
    "badge",
    PALETTE[label] || "badge muted"
  )

  return (
    <span
      className={className}
      role="status"
      aria-label={`Status ${label}`}
    >
      {label}
    </span>
  )
}

StatusBadge.propTypes = {
  value: PropTypes.string,
}
