import { useAppData } from '../context/useAppData.js'
import SectionHeader from '../components/SectionHeader.jsx'
import StatusBadge from '../components/StatusBadge.jsx'

export default function UnitTracking() {
  const { units } = useAppData()

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Live Tracking"
        title="GPS Telemetry & Status"
        action={<button className="ghost-button">Open Live Map</button>}
      />
      <div className="section-grid">
        <div className="panel map-panel">
          <div className="map-placeholder">
            <div>
              <p className="eyebrow">Live GIS Feed</p>
              <h3>Metro Coverage Grid</h3>
              <p>
                Real-time positioning from CAD telematics. Overlay hospital routing,
                traffic, and staging zones.
              </p>
            </div>
            <div className="map-grid">
              {units.map((unit) => (
                <div key={unit.unit_identifier} className="map-node">
                  <span>{unit.unit_identifier}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Fleet" title="Unit Status" />
          <div className="stack">
            {units.map((unit) => (
              <div className="list-row" key={unit.unit_identifier}>
                <div>
                  <p className="list-title">{unit.unit_identifier}</p>
                  <p className="list-sub">
                    Lat {unit.latitude?.toFixed?.(2)}, Lon {unit.longitude?.toFixed?.(2)}
                  </p>
                </div>
                <StatusBadge value={unit.status} />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
