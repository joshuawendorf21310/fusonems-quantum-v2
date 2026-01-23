export default function StatCard({ label, value, delta, footnote }) {
  return (
    <div className="stat-card">
      <p className="stat-label">{label}</p>
      <div className="stat-row">
        <h3>{value}</h3>
        {delta ? <span className="stat-delta">{delta}</span> : null}
      </div>
      {footnote ? <p className="stat-footnote">{footnote}</p> : null}
    </div>
  )
}
