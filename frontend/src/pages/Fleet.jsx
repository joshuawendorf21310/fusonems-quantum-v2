import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import {
  fallbackFleetVehicles,
  fallbackFleetMaintenance,
  fallbackFleetInspections,
  fallbackFleetTelemetry,
} from '../data/fallback.js'

const vehicleColumns = [
  { key: 'vehicle_id', label: 'Vehicle' },
  { key: 'call_sign', label: 'Call Sign' },
  { key: 'vehicle_type', label: 'Type' },
  { key: 'status', label: 'Status' },
  { key: 'location', label: 'Location' },
]

const maintenanceColumns = [
  { key: 'service_type', label: 'Service' },
  { key: 'status', label: 'Status' },
  { key: 'due_mileage', label: 'Due Mileage' },
  { key: 'notes', label: 'Notes' },
]

const inspectionColumns = [
  { key: 'status', label: 'Status' },
  { key: 'findings', label: 'Findings' },
  { key: 'performed_by', label: 'Inspector' },
]

const telemetryColumns = [
  { key: 'latitude', label: 'Lat' },
  { key: 'longitude', label: 'Lng' },
  { key: 'speed', label: 'Speed' },
  { key: 'odometer', label: 'Odometer' },
]

export default function Fleet() {
  return (
    <div className="page">
      <SectionHeader
        eyebrow="Fleet Operations"
        title="Vehicles, Maintenance, Telemetry"
        action={<button className="primary-button">Add Vehicle</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Registry" title="Fleet Vehicles" />
          <DataTable columns={vehicleColumns} rows={fallbackFleetVehicles} emptyState="No vehicles." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Maintenance Risk"
            model="fleet-watch"
            version="1.1"
            level="ADVISORY"
            message="1 vehicle due for oil change within 500 miles."
            reason="Mileage + downtime threshold"
          />
          <div className="note-card">
            <p className="note-title">Safety Alerts</p>
            <p className="note-body">No critical safety events in the last 24 hours.</p>
          </div>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Maintenance" title="Service Schedule" />
          <DataTable columns={maintenanceColumns} rows={fallbackFleetMaintenance} emptyState="No maintenance." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Inspections" title="Daily Checks" />
          <DataTable columns={inspectionColumns} rows={fallbackFleetInspections} emptyState="No inspections." />
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Telemetry" title="Live Vehicle Signals" />
        <DataTable columns={telemetryColumns} rows={fallbackFleetTelemetry} emptyState="No telemetry yet." />
      </div>
    </div>
  )
}
