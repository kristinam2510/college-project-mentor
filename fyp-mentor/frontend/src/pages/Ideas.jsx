import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import PipelineRail from '../components/PipelineRail'

export default function Ideas() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [selected, setSelected] = useState(null)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    api.getProject(projectId).then(setProject).catch((e) => setError(String(e)))
  }, [projectId])

  async function confirmSelection() {
    if (selected === null) return
    setRunning(true)
    setError(null)
    try {
      await api.selectIdea(projectId, selected)
      navigate(`/project/${projectId}`)
    } catch (err) {
      setError('Pipeline failed. Check backend logs / API key, then try again.')
      console.error(err)
      setRunning(false)
    }
  }

  if (running) {
    return (
      <>
        <PipelineRail activeIndex={1} />
        <div className="content loading-screen">
          <div className="pulse" />
          <div className="loading-label">
            Running research, gap detection, dataset search, architecture and roadmap agents…
            <br />This takes a minute — it's making several real API calls.
          </div>
        </div>
      </>
    )
  }

  if (!project) return <div className="content no-rail">Loading…</div>

  return (
    <div className="content no-rail">
      <div className="eyebrow">Step 02 — Choose a direction</div>
      <h1>Pick one to run with</h1>
      <p className="subtitle">
        Scored on innovation, difficulty, and industry relevance for {project.domain} at {project.difficulty} difficulty.
        Once selected, everything else is generated automatically.
      </p>

      {error && <div className="error-banner">{error}</div>}

      <div className="idea-grid">
        {project.ideas?.map((idea, i) => (
          <div
            key={i}
            className={`idea-card ${selected === i ? 'selected' : ''}`}
            onClick={() => setSelected(i)}
          >
            <div className="idea-title">{idea.title}</div>
            <div className="idea-desc">{idea.description}</div>
            <div className="score-row">
              <span className="score">Innovation <b>{idea.innovation_score}/10</b></span>
              <span className="score">Difficulty <b>{idea.difficulty_score}/10</b></span>
              <span className="score">Relevance <b>{idea.industry_relevance_score}/10</b></span>
            </div>
            <div className="tech-tags">
              {idea.key_technologies?.map((t) => <span className="tag" key={t}>{t}</span>)}
            </div>
          </div>
        ))}
      </div>

      <div style={{ marginTop: 28 }}>
        <button className="btn-primary" disabled={selected === null} onClick={confirmSelection}>
          Run pipeline on this idea →
        </button>
      </div>
    </div>
  )
}
