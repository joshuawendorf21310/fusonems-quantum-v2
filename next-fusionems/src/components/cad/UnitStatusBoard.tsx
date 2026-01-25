import { CadUnit } from './DualScreenCAD'

type UnitStatusBoardProps = {
  units: CadUnit[]
  activeUnitId: string | null
  onSelectUnit: (unitId: string) => void
  onAssign: (callId: number, unitIdentifier: string) => Promise<void>
}

export default function UnitStatusBoard({
  units,
  activeUnitId,
  onSelectUnit,
  onAssign,
}: UnitStatusBoardProps) {
  return (
    <div className="panel cad-panel">
      <div className="cad-panel-header">
        <div>
          <p className="panel-eyebrow">Units</p>
          <h3>Unit Status Board</h3>
        </div>
      </div>
      <div className="cad-list">
        {units.map((unit) => (
          <div
            key={unit.unit_identifier}
            className={`cad-card cad-unit ${activeUnitId === unit.unit_identifier ? 'cad-card-active' : ''}`}
            onClick={() => onSelectUnit(unit.unit_identifier)}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault()
              const callId = Number(event.dataTransfer.getData('text/plain'))
              if (Number.isFinite(callId) && callId > 0) {
                onAssign(callId, unit.unit_identifier)
              }
            }}
          >
            <div className="cad-card-header">
              <span className="cad-unit-label">Unit {unit.unit_identifier}</span>
              <span className="cad-status">{unit.status}</span>
            </div>
            <p className="cad-sub">
              Lat {unit.latitude.toFixed(2)} · Lon {unit.longitude.toFixed(2)}
            </p>
            <p className="cad-meta">Drop a call to dispatch</p>
          </div>
        ))}
        {!units.length && <p className="empty-state">No units available.</p>}
      </div>
    </div>
  )
}
