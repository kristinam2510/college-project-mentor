import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

export default function Intake() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    domain: '',
    sector: '',
    difficulty: 'Medium',
    duration_months: 4,
    team_size: 2,
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const update = (key, value) => setForm((f) => ({ ...f, [key]: value }))

  async function handleSubmit(e) {
    e.preventDefault()
    if (!form.domain.trim()) {
      setError('Enter a domain to continue.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const project = await api.createProject(form)
      navigate(`/ideas/${project.id}`)
    } catch (err) {
      setError('Could not generate ideas. Check that the backend is running and GROQ_API_KEY is set.')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="content no-rail loading-screen">
        <div className="pulse" />
        <div className="loading-label">Generating project ideas for {form.domain || 'your domain'}…</div>
      </div>
    )
  }

  return (
    <div className="content no-rail">
      <div className="eyebrow">Step 01 — Intake</div>
      <h1>What are you building?</h1>
      <p className="subtitle">
        Four inputs is all it takes. Everything after this — research, gap analysis,
        architecture, and a month-by-month plan — runs on its own once you pick an idea.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="field" style={{ maxWidth: 560 }}>
          <label>Domain</label>
          <input
            placeholder="e.g. Computer Vision, NLP, IoT, Healthcare Informatics"
            value={form.domain}
            onChange={(e) => update('domain', e.target.value)}
          />
        </div>

        <div className="field" style={{ maxWidth: 560 }}>
          <label>Sector (optional)</label>
          <input
            placeholder="e.g. Healthcare, Finance, E-commerce, Education"
            value={form.sector}
            onChange={(e) => update('sector', e.target.value)}
          />
        </div>

        <div className="form-grid">
          <div className="field">
            <label>Difficulty</label>
            <select value={form.difficulty} onChange={(e) => update('difficulty', e.target.value)}>
              <option>Easy</option>
              <option>Medium</option>
              <option>Hard</option>
            </select>
          </div>
          <div className="field">
            <label>Team size</label>
            <input
              type="number" min={1} max={8}
              value={form.team_size}
              onChange={(e) => update('team_size', parseInt(e.target.value || '1', 10))}
            />
          </div>
          <div className="field">
            <label>Duration (months)</label>
            <input
              type="number" min={1} max={12}
              value={form.duration_months}
              onChange={(e) => update('duration_months', parseInt(e.target.value || '1', 10))}
            />
          </div>
        </div>

        <button className="btn-primary" type="submit">Generate project ideas →</button>
      </form>
    </div>
  )
}