export default function AdvisoryPanel({ title, model, version, level, message, reason }) {
  const modelStamp = version ? `${model} v${version}` : model
  return (
    <div className="advisory-panel">
      <div className="advisory-header">
        <span className="advisory-title">{title}</span>
        <span className="advisory-badge">{level}</span>
      </div>
      <p className="advisory-text">{message}</p>
      <p className="advisory-meta">Model: {modelStamp}</p>
      {reason ? <p className="advisory-meta">Why: {reason}</p> : null}
    </div>
  )
}
