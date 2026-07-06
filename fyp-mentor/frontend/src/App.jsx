import { Outlet } from 'react-router-dom'

export default function App() {
  return (
    <div className="app-shell">
      <div className="topbar">
        <div className="brand">
          <span>FYP<span className="dot">.</span>Mentor</span>
          <small>project pipeline</small>
        </div>
      </div>
      <div className="main">
        <Outlet />
      </div>
    </div>
  )
}
