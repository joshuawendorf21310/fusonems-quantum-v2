import { useAppData } from '../context/AppContext.jsx'
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
          description="AI forecast for the next 8 hours across all zones."
          data={[6, 5, 9, 12, 8, 4, 6, 5]}
        />
        <div className="panel">
          <SectionHeader eyebrow="AI Recommendations" title="Actionable Guidance" />
          <div className="stack">
            {insights.map((insight, index) => (
              <div className="insight-card" key={`${insight.category}-${index}`}>
                <p className="insight-category">{insight.category}</p>
                <h4>{insight.prompt}</h4>
                <p>{insight.response}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
