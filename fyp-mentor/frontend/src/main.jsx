import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './styles.css'
import App from './App.jsx'
import Projects from './pages/Projects.jsx'
import Intake from './pages/Intake.jsx'
import Ideas from './pages/Ideas.jsx'
import Dashboard from './pages/Dashboard.jsx'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Projects />} />
          <Route path="new" element={<Intake />} />
          <Route path="ideas/:projectId" element={<Ideas />} />
          <Route path="project/:projectId" element={<Dashboard />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
)