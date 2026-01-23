import { useAppData } from '../context/useAppData.js'
import SectionHeader from '../components/SectionHeader.jsx'
import ChartPanel from '../components/ChartPanel.jsx'

export default function AiConsole() {
  const { insights } = useAppData()

  return (
    <div className="page">
      <SectionHeader
        eyebrow="AI Console"
        title="Predictive Operations & Optimization"
        action={<button className="ghost-button">Run Forecast</button>}
      />

      <div className="section-grid">
        <ChartPanel
          title="Predicted Call Volume"
          description="Forecasts appear after call volume history is available."
          data={[]}
          emptyState="No forecast yet. Connect CAD history to enable predictions."
        />
        <div className="panel">
          <SectionHeader eyebrow="AI Recommendations" title="Actionable Guidance" />
          <div className="stack">
            {insights.length > 0 ? (
              insights.map((insight, index) => (
                <div className="insight-card" key={`${insight.category}-${index}`}>
                  <p className="insight-category">{insight.category}</p>
                  <h4>{insight.prompt}</h4>
                  <p>{insight.response}</p>
                </div>
              ))
            ) : (
              <div className="note-card">
                <p className="note-title">No recommendations yet</p>
                <p className="note-body">
                  Enable policy rules and event streams to generate deterministic guidance.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
