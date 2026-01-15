import { useAppData } from '../context/AppContext.jsx'

export default function TopBar() {
  const { lastSync, refreshAll } = useAppData()

  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">EMS Operations</p>
        <h1>Quantum Command Center</h1>
      </div>
      <div className="topbar-actions">
        <div className="sync">
          <span className="sync-dot" />
          <div>
            <p className="sync-label">Last sync</p>
            <p className="sync-time">{lastSync || 'Just now'}</p>
          </div>
        </div>
        <button className="primary-button" type="button" onClick={refreshAll}>
          Refresh Live Feeds
        </button>
      </div>
    </header>
  )
}
