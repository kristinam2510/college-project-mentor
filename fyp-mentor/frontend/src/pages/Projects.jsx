import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function Projects() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    api.listProjects().then((p) => {
      setProjects(p)
      setLoading(false)
    })
  }, [])

  async function handleDelete(id, title) {
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return
    await api.deleteProject(id)
    setProjects((prev) => prev.filter((p) => p.id !== id))
  }

  if (loading) return <div className="content no-rail">Loading projects…</div>

  return (
    <div className="content no-rail" style={{ width: '100%' }}>
      <div className="eyebrow">FYP Mentor</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
        <h1 style={{ margin: 0 }}>My Projects</h1>
        <button className="btn-primary" onClick={() => navigate('/new')}>+ New Project</button>
      </div>

      {projects.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 56, color: 'var(--paper-dim)' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>📂</div>
          <div style={{ fontSize: 15, marginBottom: 8 }}>No projects yet</div>
          <div style={{ fontSize: 13 }}>Start by creating a new project above.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {projects.map((p) => (
            <div
              key={p.id}
              className="card"
              style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 24 }}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 15, marginBottom: 4 }}>
                  {p.title || 'Untitled Project'}
                </div>
                <div
                  style={{
                    fontSize: 13,
                    color: 'var(--paper-dim)',
                    marginBottom: 10,
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {p.description || 'No description yet'}
                </div>
                <span
                  style={{
                    fontSize: 11,
                    fontFamily: 'var(--font-mono)',
                    padding: '3px 10px',
                    borderRadius: 4,
                    background: p.approved
                      ? 'rgba(0, 200, 100, 0.12)'
                      : 'rgba(200, 150, 0, 0.12)',
                    color: p.approved ? '#00c864' : '#c89600',
                    border: `1px solid ${p.approved ? 'rgba(0,200,100,0.25)' : 'rgba(200,150,0,0.25)'}`,
                  }}
                >
                  {p.approved ? '✓ Approved — Progress unlocked' : '⏳ Pending your approval'}
                </span>
              </div>

              <div style={{ display: 'flex', gap: 10, flexShrink: 0 }}>
                <button className="btn-primary" onClick={() => navigate(`/project/${p.id}`)}>
                  Open
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => handleDelete(p.id, p.title)}
                  style={{ color: '#ff5555' }}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}