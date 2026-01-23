import PropTypes from "prop-types"

export default function StatCard({ label, value, delta, footnote }) {
  const labelId =
    typeof label === "string"
      ? `stat-label-${label.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`
      : undefined

  return (
    <section
      className="stat-card"
      role="group"
      aria-labelledby={labelId}
    >
      <p
        id={labelId}
        className="stat-label"
      >
        {label}
      </p>

      <div className="stat-row">
        <h3 className="stat-value">
          {value ?? "—"}
        </h3>

        {delta !== undefined && delta !== null && (
          <span
            className="stat-delta"
            aria-label={`Change ${delta}`}
          >
            {delta}
          </span>
        )}
      </div>

      {footnote && (
        <p className="stat-footnote">
          {footnote}
        </p>
      )}
    </section>
  )
}

StatCard.propTypes = {
  label: PropTypes.node.isRequired,
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number,
  ]),
  delta: PropTypes.node,
  footnote: PropTypes.node,
}