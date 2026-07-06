import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'

const TABS = ['Overview', 'Research', 'Gaps', 'Datasets', 'Architecture', 'Roadmap', 'Progress', 'Mentor']

export default function Dashboard() {
  const { projectId } = useParams()
  const navigate = useNavigate()
  const [project, setProject] = useState(null)
  const [tasks, setTasks] = useState([])
  const [risk, setRisk] = useState(null)
  const [mentor, setMentor] = useState(null)
  const [mentorLoading, setMentorLoading] = useState(false)
  const [mentorError, setMentorError] = useState(false)
  const [approving, setApproving] = useState(false)
  const [tab, setTab] = useState('Overview')

  const refreshTasks = useCallback(() => {
    api.getTasks(projectId).then(setTasks)
  }, [projectId])

  useEffect(() => {
    api.getProject(projectId).then(setProject)
    refreshTasks()
    api.getRisk(projectId).then(setRisk)
  }, [projectId, refreshTasks])

  async function toggleTask(task) {
    const markingDone = task.status !== 'done'

    if (markingDone) {
      const confirmed = window.confirm(
        `Before marking "${task.title}" as done — have you checked in with your team/supervisor and noted what you completed?`
      )
      if (!confirmed) return
    }

    const newStatus = markingDone ? 'done' : 'pending'
    await api.updateTask(task.id, newStatus)

    // Refresh task list and risk score
    refreshTasks()
    api.getRisk(projectId).then(setRisk)

    // Auto-refresh mentor advice so it reflects the new progress
    setMentor(null)
    loadMentor()
  }

  async function loadMentor() {
    setMentorLoading(true)
    setMentorError(false)
    try {
      const result = await api.getMentor(projectId)
      setMentor(result)
    } catch (e) {
      setMentorError(true)
    } finally {
      setMentorLoading(false)
    }
  }

  async function handleApprove() {
    setApproving(true)
    try {
      await api.approveProject(projectId)
      // Refresh project so approved flag updates and Progress tab unlocks
      const fresh = await api.getProject(projectId)
      setProject(fresh)
    } finally {
      setApproving(false)
    }
  }

  if (!project) return <div className="content no-rail">Loading…</div>

  const research = project.research
  const gaps = project.gaps
  const datasets = project.datasets
  const architecture = project.architecture
  const roadmap = project.roadmap
  const isApproved = project.approved

  // All pipeline sections must be present before approve button shows
  const pipelineComplete = !!(research && gaps && datasets && architecture && roadmap)

  const doneCount = tasks.filter((t) => t.status === 'done').length

  return (
    <div className="content no-rail" style={{ width: '100%' }}>
      <div className="eyebrow" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span
          style={{ cursor: 'pointer', color: 'var(--paper-dim)', fontSize: 12 }}
          onClick={() => navigate('/')}
        >
          ← My Projects
        </span>
        {isApproved ? (
          <span style={{
            fontSize: 11, fontFamily: 'var(--font-mono)',
            padding: '3px 10px', borderRadius: 4,
            background: 'rgba(0,200,100,0.12)', color: '#00c864',
            border: '1px solid rgba(0,200,100,0.25)',
          }}>
            ✓ Approved
          </span>
        ) : pipelineComplete ? (
          <button className="btn-primary" onClick={handleApprove} disabled={approving}>
            {approving ? 'Saving…' : '✓ Approve & Save Project'}
          </button>
        ) : null}
      </div>

      <h1>{project.title}</h1>
      <p className="subtitle">{project.description}</p>

      {/* Approval banner — visible until approved */}
      {!isApproved && pipelineComplete && (
        <div style={{
          background: 'rgba(200,150,0,0.1)',
          border: '1px solid rgba(200,150,0,0.3)',
          borderRadius: 8,
          padding: '12px 16px',
          marginBottom: 20,
          fontSize: 13,
          color: '#c89600',
        }}>
          Review the Research, Gaps, Datasets, Architecture and Roadmap tabs — when you're happy, click <strong>Approve & Save Project</strong> above to unlock the Progress tab.
        </div>
      )}

      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? 'active' : ''} ${(t === 'Progress' || t === 'Mentor') && !isApproved ? 'disabled' : ''}`}
            style={(t === 'Progress' || t === 'Mentor') && !isApproved ? { opacity: 0.4, cursor: 'not-allowed' } : {}}
            onClick={() => {
              if ((t === 'Progress' || t === 'Mentor') && !isApproved) return
              setTab(t)
              if (t === 'Mentor' && !mentor) loadMentor()
            }}
          >
            {t}{(t === 'Progress' || t === 'Mentor') && !isApproved ? ' 🔒' : ''}
          </button>
        ))}
      </div>

      {tab === 'Overview' && risk && (
        <div>
          <div className="stat-row">
            <div className={`card stat-card risk-${risk.risk_level}`}>
              <div className="stat-value">{risk.risk_level}</div>
              <div className="stat-label">Risk level ({risk.risk_score}/100)</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">{risk.success_probability}%</div>
              <div className="stat-label">Success probability</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">{doneCount}/{tasks.length}</div>
              <div className="stat-label">Tasks completed</div>
            </div>
            <div className="card stat-card">
              <div className="stat-value">{risk.expected_completion_date}</div>
              <div className="stat-label">Expected completion</div>
            </div>
          </div>
          <div className="card">
            <h2>Why this assessment</h2>
            <ul style={{ paddingLeft: 18, fontSize: 13.5 }}>
              {risk.explanation_factors.map((f, i) => <li key={i} style={{ marginBottom: 8 }}>{f}</li>)}
            </ul>
          </div>
        </div>
      )}

      {tab === 'Research' && research && (
        <div className="card">
          <h2>Research trends</h2>
          <ul style={{ paddingLeft: 18, fontSize: 13.5, marginBottom: 24 }}>
            {research.survey?.research_trends?.map((t, i) => <li key={i} style={{ marginBottom: 6 }}>{t}</li>)}
          </ul>
          <h2>State of the art</h2>
          <div className="tech-tags" style={{ marginBottom: 24 }}>
            {research.survey?.state_of_the_art_techniques?.map((t) => <span className="tag" key={t}>{t}</span>)}
          </div>
          <h2>Top papers</h2>
          {research.survey?.top_papers?.map((p, i) => (
            <div className="paper-row" key={i}>
              <div className="title">{p.title}</div>
              <div className="meta">{p.why_relevant}{p.url ? ` — ` : ''}{p.url && <a href={p.url} target="_blank" rel="noreferrer">source</a>}</div>
            </div>
          ))}
        </div>
      )}

      {tab === 'Gaps' && gaps && (
        <div>
          <div className="card" style={{ marginBottom: 20 }}>
            <h2>Method distribution across retrieved papers</h2>
            {gaps.method_distribution?.map((m) => (
              <div className="dist-bar-row" key={m.method}>
                <span className="dist-label">{m.method}</span>
                <span className="dist-bar-track"><span className="dist-bar-fill" style={{ width: `${m.percentage}%` }} /></span>
                <span className="dist-pct">{m.percentage}%</span>
              </div>
            ))}
          </div>
          <h2>Identified research gaps</h2>
          {gaps.gaps?.map((g, i) => (
            <div className="gap-card" key={i}>
              <div className="statement">{g.gap_statement}</div>
              <div className="meta-line">{g.evidence}</div>
              <div className="meta-line">{g.suggested_approach}</div>
              <span className={`feasibility ${g.feasibility_for_student}`}>{g.feasibility_for_student} feasibility</span>
            </div>
          ))}
        </div>
      )}

      {tab === 'Datasets' && (
        <div className="idea-grid">
          {datasets?.map((d, i) => (
            <div className="card" key={i}>
              <div className="idea-title">{d.name}</div>
              <div className="idea-desc">{d.source} · {d.size_description}</div>
              <div className="score-row" style={{ marginTop: 10 }}>
                <span className="score">Quality <b>{d.quality_score}/10</b></span>
              </div>
              <div className="meta" style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--paper-dim)', marginTop: 6 }}>
                {d.annotation_format}
              </div>
              {d.url && <a href={d.url} target="_blank" rel="noreferrer" style={{ fontSize: 12.5 }}>View dataset →</a>}
            </div>
          ))}
        </div>
      )}

      {tab === 'Architecture' && architecture && (
        <div className="card">
          <h2>Components</h2>
          {architecture.components?.map((c, i) => (
            <div className="paper-row" key={i}>
              <div className="title">{c.name} <span style={{ color: 'var(--paper-dim)', fontWeight: 400 }}>— {c.technology_choice}</span></div>
              <div className="meta">{c.role}. {c.justification}</div>
            </div>
          ))}
          <h2 style={{ marginTop: 20 }}>Data flow</h2>
          <ol style={{ paddingLeft: 18, fontSize: 13.5 }}>
            {architecture.data_flow?.map((step, i) => <li key={i} style={{ marginBottom: 6 }}>{step}</li>)}
          </ol>
          <h2 style={{ marginTop: 20 }}>Summary</h2>
          <p style={{ fontSize: 13.5, color: 'var(--paper-dim)' }}>{architecture.tech_stack_summary}</p>
        </div>
      )}

      {tab === 'Roadmap' && roadmap && (
        <div>
          {roadmap.months?.map((m) => (
            <div className="roadmap-month" key={m.month}>
              <div className="month-tag">MONTH {m.month}</div>
              <div className="month-body">
                <div className="theme">{m.theme}</div>
                <div className="milestone">Milestone: {m.milestone}</div>
                <ul style={{ paddingLeft: 18, fontSize: 13, color: 'var(--paper-dim)' }}>
                  {m.tasks?.map((t, i) => <li key={i}>{t}</li>)}
                </ul>
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === 'Progress' && (
        <div className="card">
          <h2>Task board ({doneCount}/{tasks.length} complete)</h2>
          <ul className="task-list">
            {(() => {
              // Assign each task its own week number based on position within its month
              const monthCounters = {}
              return tasks.map((t) => {
                if (monthCounters[t.month] === undefined) monthCounters[t.month] = 0
                const posInMonth = monthCounters[t.month]
                monthCounters[t.month]++
                const weekNum = (t.month - 1) * 4 + posInMonth + 1
                return (
                  <li key={t.id} className={`task-item ${t.status === 'done' ? 'done' : ''}`}>
                    <span className={`task-checkbox ${t.status === 'done' ? 'done' : ''}`} onClick={() => toggleTask(t)} />
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--paper-dim)', width: 60 }}>Week {weekNum}</span>
                    <span className="task-title">{t.title}</span>
                  </li>
                )
              })
            })()}
          </ul>
        </div>
      )}

      {tab === 'Mentor' && (
        <div className="card mentor-card">
          {mentorLoading && <div className="loading-label">Reviewing your progress…</div>}
          {!mentorLoading && mentorError && (
            <div style={{ color: '#ff5555', fontSize: 13, marginBottom: 12 }}>
              Failed to load mentor advice. Check your API key / rate limit and try again.
            </div>
          )}
          {!mentorLoading && mentor && (
            <>
              <div style={{ marginBottom: 12 }}>
                <span style={{
                  fontSize: 11, fontFamily: 'var(--font-mono)',
                  padding: '3px 10px', borderRadius: 4,
                  background: mentor.pace_status === 'ahead'
                    ? 'rgba(0,200,100,0.12)'
                    : mentor.pace_status === 'behind'
                    ? 'rgba(220,50,50,0.12)'
                    : 'rgba(100,150,255,0.12)',
                  color: mentor.pace_status === 'ahead'
                    ? '#00c864'
                    : mentor.pace_status === 'behind'
                    ? '#ff5555'
                    : '#6496ff',
                  border: `1px solid ${mentor.pace_status === 'ahead'
                    ? 'rgba(0,200,100,0.25)'
                    : mentor.pace_status === 'behind'
                    ? 'rgba(220,50,50,0.25)'
                    : 'rgba(100,150,255,0.25)'}`,
                }}>
                  {mentor.pace_status === 'ahead' ? '↑ Ahead of schedule'
                    : mentor.pace_status === 'behind' ? '↓ Behind schedule'
                    : '→ On track'}
                </span>
              </div>
              <div className="headline" style={{ marginBottom: 16 }}>{mentor.headline}</div>
              <h3 style={{ fontSize: 12, fontFamily: 'var(--font-mono)', color: 'var(--paper-dim)', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>Next steps</h3>
              <ul style={{ paddingLeft: 18, marginBottom: 20 }}>
                {mentor.next_steps?.map((s, i) => <li key={i} style={{ marginBottom: 6, fontSize: 13.5 }}>{s}</li>)}
              </ul>
              {mentor.biggest_risk && (
                <div style={{
                  background: mentor.pace_status === 'ahead'
                    ? 'rgba(200,150,0,0.08)'
                    : 'rgba(220,50,50,0.08)',
                  border: `1px solid ${mentor.pace_status === 'ahead'
                    ? 'rgba(200,150,0,0.2)'
                    : 'rgba(220,50,50,0.2)'}`,
                  borderRadius: 6, padding: '10px 14px', marginBottom: 16,
                }}>
                  <span style={{
                    fontSize: 11, fontFamily: 'var(--font-mono)',
                    color: mentor.pace_status === 'ahead' ? '#c89600' : '#ff5555',
                    textTransform: 'uppercase', letterSpacing: 1
                  }}>
                    {mentor.pace_status === 'ahead' ? '⚡ Watch out for' : '⚠ Biggest risk'}
                  </span>
                  <div style={{ fontSize: 13, marginTop: 4, color: 'var(--paper-dim)' }}>{mentor.biggest_risk}</div>
                </div>
              )}
              <div className="encouragement" style={{ fontStyle: 'italic', color: 'var(--paper-dim)', fontSize: 13 }}>{mentor.encouragement}</div>
            </>
          )}
          <div style={{ marginTop: 18 }}>
            <button className="btn-secondary" onClick={loadMentor}>Refresh status</button>
          </div>
        </div>
      )}
    </div>
  )
}