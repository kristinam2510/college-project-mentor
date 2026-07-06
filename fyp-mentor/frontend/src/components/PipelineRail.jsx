const STAGES = [
  'Idea Selection',
  'Research Survey',
  'Gap Detection',
  'Datasets',
  'Architecture',
  'Roadmap',
]

export default function PipelineRail({ activeIndex }) {
  return (
    <div className="pipeline-rail">
      {STAGES.map((label, i) => (
        <div key={label} className={`stage ${i === activeIndex ? 'active' : i < activeIndex ? 'done' : ''}`}>
          <span className="stage-marker" />
          <span className="stage-label">
            <span className="stage-num">{String(i + 1).padStart(2, '0')}</span>
            {label}
          </span>
        </div>
      ))}
    </div>
  )
}
