export default function ChartPanel({ title, description, data = [], emptyState = 'No chart data yet.' }) {
  const hasData = Array.isArray(data) && data.length > 0
  return (
    <div className="chart-panel">
      <div className="chart-meta">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <div className="chart">
        {hasData ? (
          data.map((value, index) => (
            <div
              key={`${value}-${index}`}
              className="chart-bar"
              style={{ height: `${value * 6 + 10}px` }}
            >
              <span>{value}</span>
            </div>
          ))
        ) : (
          <div className="chart-empty">{emptyState}</div>
        )}
      </div>
    </div>
  )
}
