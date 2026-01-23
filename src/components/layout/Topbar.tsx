"use client"

import Link from "next/link"

export default function Topbar() {
  return (
    <header className="topbar" aria-label="Platform controls">
      <div className="topbar-title">
        <p className="eyebrow">Command Gate</p>
        <h1>Platform Control</h1>
      </div>
      <div className="topbar-search">
        <input type="search" placeholder="Search portals, audits, roles..." aria-label="Search platform" />
        <button type="button" aria-label="Search command center">
          🔍
        </button>
      </div>
      <div className="topbar-actions">
        <span className="org-pill" aria-label="Organization name">
          Orion EMS
        </span>
        <span className="notification-dot" role="status" aria-label="2 new notifications">
          ✉️ 2
        </span>
        <span className="avatar" aria-hidden="true">
          👤
        </span>
        <Link className="logout" href="/coming-soon">
          Logout
        </Link>
      </div>
    </header>
  )
}
