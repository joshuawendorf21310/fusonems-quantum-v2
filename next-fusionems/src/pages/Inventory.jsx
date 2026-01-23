import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import {
  fallbackInventoryItems,
  fallbackInventoryMovements,
  fallbackRigChecks,
} from '../data/fallback.js'

const itemColumns = [
  { key: 'name', label: 'Item' },
  { key: 'category', label: 'Category' },
  { key: 'par_level', label: 'Par' },
  { key: 'quantity_on_hand', label: 'On Hand' },
  { key: 'location', label: 'Location' },
  { key: 'status', label: 'Status' },
]

const movementColumns = [
  { key: 'movement_type', label: 'Move' },
  { key: 'quantity', label: 'Qty' },
  { key: 'from_location', label: 'From' },
  { key: 'to_location', label: 'To' },
  { key: 'reason', label: 'Reason' },
]

const rigColumns = [
  { key: 'unit_id', label: 'Unit' },
  { key: 'status', label: 'Status' },
  { key: 'findings', label: 'Findings' },
  { key: 'performed_by', label: 'By' },
]

export default function Inventory() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Inventory"
        title="Rig Checks + Stock Control"
        action={<button className="primary-button">New Movement</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Stock" title="Inventory Items" />
          <DataTable columns={itemColumns} rows={fallbackInventoryItems} emptyState="No inventory items." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Restock Signal"
            model="supply-watch"
            version="1.4"
            level="ADVISORY"
            message="2 kits below par. Auto-restock request staged."
            reason="Par level + shift utilization"
          />
          <div className="note-card">
            <p className="note-title">Expiring Soon</p>
            <p className="note-body">4 items within 30 days of expiration.</p>
          </div>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Movements" title="Transfers + Issues" />
          <DataTable columns={movementColumns} rows={fallbackInventoryMovements} emptyState="No movements." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Rig Checks" title="Daily Logs" />
          <DataTable columns={rigColumns} rows={fallbackRigChecks} emptyState="No rig checks." />
        </div>
      </div>
    </div>
  )
}
