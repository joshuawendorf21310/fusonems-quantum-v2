const palette = {
  Critical: 'badge critical',
  High: 'badge high',
  Routine: 'badge routine',
  Dispatched: 'badge active',
  'En Route': 'badge active',
  'On Scene': 'badge focus',
  Cleared: 'badge muted',
  Queued: 'badge muted',
  Scheduled: 'badge muted',
  Swapped: 'badge focus',
  Available: 'badge active',
  Open: 'badge high',
  Pending: 'badge routine',
}

export default function StatusBadge({ value }) {
  const className = palette[value] || 'badge muted'
  return <span className={className}>{value}</span>
}
