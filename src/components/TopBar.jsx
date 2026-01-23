import PropTypes from "prop-types"
import { useAppData } from "../context/useAppData.js"
import { useAuth } from "../context/useAuth.js"

export default function TopBar({ title = "Quantum Command Center" }) {
  const { refreshAll } = useAppData()
  const { user } = useAuth()

  return (
    <div className="topbar">
      <div className="topbar-content">
        <div className="topbar-left">
          <h1 className="topbar-title">
            {title}
          </h1>
        </div>

        <div className="topbar-right">
          {user && (
            <span className="topbar-user">
              {user.display_name || user.email || "User"}
            </span>
          )}

          <button
            className="primary-button topbar-refresh"
            type="button"
            onClick={refreshAll}
            aria-label="Refresh system data"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  )
}

TopBar.propTypes = {
  title: PropTypes.string,
}
