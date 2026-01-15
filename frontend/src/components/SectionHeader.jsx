export default function SectionHeader({ eyebrow, title, action }) {
  return (
    <div className="section-header">
      <div>
        {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
        <h2>{title}</h2>
      </div>
      {action ? <div className="section-action">{action}</div> : null}
    </div>
  )
}
