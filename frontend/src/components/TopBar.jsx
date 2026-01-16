import { useAppData } from '../context/useAppData.js'
import { useAuth } from '../context/useAuth.js'

export default function TopBar() {
  const { lastSync, refreshAll, trainingStatus } = useAppData()
  const { smartMode } = useAuth()
  const trainingActive =
    trainingStatus?.org_mode === 'ENABLED' || trainingStatus?.user_mode

  return (
    <header className="topbar">
      {trainingActive ? (
        <div className="training-banner">
          TRAINING MODE — All data is segregated and exports are disabled.
        </div>
      ) : null}
      <div className="topbar-content">
        <div>
          <p className="eyebrow">EMS Operations</p>
          <h1>Quantum Command Center</h1>
        </div>
        <div className="topbar-actions">
          <div className="status-pill">System Alive</div>
          <div className={`status-pill ${smartMode ? 'focus' : 'muted'}`}>
            Smart Mode {smartMode ? 'On' : 'Off'}
          </div>
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
      </div>
    </header>
  )
}
