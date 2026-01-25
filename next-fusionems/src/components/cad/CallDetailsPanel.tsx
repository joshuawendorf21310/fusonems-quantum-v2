import { useEffect, useState } from 'react'
import { CadCall, CadUnit } from './DualScreenCAD'

type CallDetailsPanelProps = {
  call: CadCall | null
  units: CadUnit[]
  activeUnit: CadUnit | null
  onAssign: (callId: number, unitIdentifier: string) => Promise<void>
  onStatusChange: (status: string) => Promise<void>
}

const statusOptions = ['Enroute', 'OnScene', 'Transport', 'Available']

export default function CallDetailsPanel({
  call,
  units,
  activeUnit,
  onAssign,
  onStatusChange,
}: CallDetailsPanelProps) {
  const [selectedUnit, setSelectedUnit] = useState<string>('')

  useEffect(() => {
    if (activeUnit) {
      setSelectedUnit(activeUnit.unit_identifier)
    } else {
      setSelectedUnit('')
    }
  }, [activeUnit])

  return (
    <div className="panel cad-panel cad-details-panel">
      <div className="cad-panel-header">
        <div>
          <p className="panel-eyebrow">Call Details</p>
          <h3>{call ? `Call #${call.id}` : 'Select a call'}</h3>
        </div>
        {call && <span className="cad-status">{call.status}</span>}
      </div>
      {call ? (
        <div className="cad-details-grid">
          <div>
            <p className="cad-sub">Caller</p>
            <p>{call.caller_name}</p>
          </div>
          <div>
            <p className="cad-sub">Phone</p>
            <p>{call.caller_phone}</p>
          </div>
          <div className="cad-full">
            <p className="cad-sub">Location</p>
            <p>{call.location_address}</p>
          </div>
          <div>
            <p className="cad-sub">Priority</p>
            <p>{call.priority}</p>
          </div>
          <div>
            <p className="cad-sub">ETA</p>
            <p>{call.eta_minutes ? `${call.eta_minutes} min` : 'Pending'}</p>
          </div>
          <div className="cad-full">
            <label className="cad-label" htmlFor="unit-select">
              Assign Unit
            </label>
            <div className="cad-inline">
              <select
                id="unit-select"
                value={selectedUnit}
                onChange={(event) => setSelectedUnit(event.target.value)}
              >
                <option value="" disabled>
                  Select unit
                </option>
                {units.map((unit) => (
                  <option key={unit.unit_identifier} value={unit.unit_identifier}>
                    {unit.unit_identifier} · {unit.status}
                  </option>
                ))}
              </select>
              <button
                className="primary-button"
                type="button"
                onClick={() => {
                  if (selectedUnit) {
                    onAssign(call.id, selectedUnit)
                  }
                }}
              >
                Assign
              </button>
            </div>
          </div>
          <div className="cad-full cad-status-actions">
            {statusOptions.map((status) => (
              <button key={status} type="button" className="ghost-button" onClick={() => onStatusChange(status)}>
                {status}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <p className="empty-state">Select a call from the queue to manage dispatch actions.</p>
      )}
    </div>
  )
}
