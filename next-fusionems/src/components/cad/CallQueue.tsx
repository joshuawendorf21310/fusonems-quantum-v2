import { CadCall } from './DualScreenCAD'

const priorityClass: Record<string, string> = {
  Routine: 'priority-routine',
  High: 'priority-high',
  Critical: 'priority-critical',
}

type CallQueueProps = {
  calls: CadCall[]
  selectedCallId: number | null
  onSelect: (callId: number) => void
}

export default function CallQueue({ calls, selectedCallId, onSelect }: CallQueueProps) {
  return (
    <div className="panel cad-panel">
      <div className="cad-panel-header">
        <div>
          <p className="panel-eyebrow">CAD Queue</p>
          <h3>Active Calls</h3>
        </div>
        <span className="cad-count">{calls.length}</span>
      </div>
      <div className="cad-list">
        {calls.map((call) => (
          <button
            key={call.id}
            className={`cad-card ${selectedCallId === call.id ? 'cad-card-active' : ''}`}
            onClick={() => onSelect(call.id)}
            draggable
            onDragStart={(event) => {
              event.dataTransfer.setData('text/plain', String(call.id))
            }}
          >
            <div className="cad-card-header">
              <span className={`cad-priority ${priorityClass[call.priority] ?? 'priority-routine'}`}>
                {call.priority}
              </span>
              <span className="cad-status">{call.status}</span>
            </div>
            <h4>Call #{call.id}</h4>
            <p className="cad-sub">{call.location_address}</p>
            <p className="cad-meta">
              {call.caller_name} · {call.caller_phone}
            </p>
          </button>
        ))}
        {!calls.length && <p className="empty-state">No active calls.</p>}
      </div>
    </div>
  )
}
