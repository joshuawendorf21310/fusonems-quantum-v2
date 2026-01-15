export default function ChartPanel({ title, description, data }) {
  return (
    <div className="chart-panel">
      <div className="chart-meta">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <div className="chart">
        {data.map((value, index) => (
          <div
            key={`${value}-${index}`}
            className="chart-bar"
            style={{ height: `${value * 6 + 10}px` }}
          >
            <span>{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
