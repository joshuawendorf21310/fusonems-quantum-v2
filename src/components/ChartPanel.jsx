import PropTypes from "prop-types"
import clsx from "clsx"

export default function ChartPanel({
  title,
  description,
  data = [],
  emptyState = "No chart data yet.",
  unit,
  minBarHeight = 10,
  scale = 6,
}) {
  const safeTitle = String(title || "chart").toLowerCase().replace(/[^a-z0-9]+/g, "-")
  const titleId = `chart-title-${safeTitle}`
  const descId = `chart-desc-${safeTitle}`
  const values = Array.isArray(data)
    ? data.filter((v) => Number.isFinite(v))
    : []

  const hasData = values.length > 0

  return (
    <section
      className="chart-panel"
      aria-labelledby={titleId}
      aria-describedby={description ? descId : undefined}
    >
      <header className="chart-meta">
        <h3 id={titleId}>{title}</h3>
        {description && (
          <p id={descId} className="chart-description">
            {description}
          </p>
        )}
      </header>

      <div
        className={clsx("chart", { "chart--empty": !hasData })}
        role="img"
        aria-roledescription="bar chart"
        aria-label={hasData ? title : emptyState}
      >
        {hasData ? (
          values.map((value, index) => {
            const height = Math.max(minBarHeight, value * scale)
            return (
              <div
                key={`bar-${index}`}
                className="chart-bar"
                style={{ height: `${height}px` }}
                aria-label={`Bar value ${value}${unit ? ` ${unit}` : ""}`}
              >
                <span className="chart-bar-value">
                  {value}
                  {unit ? ` ${unit}` : ""}
                </span>
              </div>
            )
          })
        ) : (
          <div className="chart-empty" role="note">
            {emptyState}
          </div>
        )}
      </div>
    </section>
  )
}

ChartPanel.propTypes = {
  title: PropTypes.string.isRequired,
  description: PropTypes.string,
  data: PropTypes.arrayOf(PropTypes.number),
  emptyState: PropTypes.string,
  unit: PropTypes.string,
  minBarHeight: PropTypes.number,
  scale: PropTypes.number,
}
