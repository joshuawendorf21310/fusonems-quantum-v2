import Sidebar from './Sidebar.jsx'
import TopBar from './TopBar.jsx'

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <TopBar />
        <main className="app-content">{children}</main>
      </div>
    </div>
  )
}
