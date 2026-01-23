import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'

const apparatusColumns = [
  { key: 'apparatus_id', label: 'Apparatus ID' },
  { key: 'apparatus_type', label: 'Type' },
  { key: 'status', label: 'Status' },
  { key: 'mileage', label: 'Mileage' },
  { key: 'readiness_score', label: 'Readiness' },
]

const inventoryColumns = [
  { key: 'item_name', label: 'Item' },
  { key: 'status', label: 'Status' },
  { key: 'quantity', label: 'Qty' },
  { key: 'notes', label: 'Notes' },
]

export default function FireApparatus() {
  const [apparatusList, setApparatusList] = useState([])
  const [inventory, setInventory] = useState([])
  const [formState, setFormState] = useState({
    apparatus_id: '',
    apparatus_type: '',
    status: 'In Service',
    mileage: 0,
    readiness_score: 100,
  })
  const [inventoryState, setInventoryState] = useState({
    apparatus_id: '',
    item_name: '',
    status: 'Ready',
    quantity: 1,
    notes: '',
  })

  const loadApparatus = async () => {
    try {
      const data = await apiFetch('/api/fire/apparatus')
      setApparatusList(data)
    } catch (error) {
      console.warn('Unable to load apparatus', error)
    }
  }

  const loadInventory = async (apparatusId) => {
    if (!apparatusId) return
    try {
      const data = await apiFetch(`/api/fire/apparatus/${apparatusId}/inventory`)
      setInventory(data)
    } catch (error) {
      console.warn('Unable to load inventory', error)
    }
  }

  useEffect(() => {
    loadApparatus()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleInventoryChange = (event) => {
    const { name, value } = event.target
    setInventoryState((prev) => ({ ...prev, [name]: value }))
  }

  const createApparatus = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/fire/apparatus', {
        method: 'POST',
        body: JSON.stringify({
          ...formState,
          mileage: Number(formState.mileage),
          readiness_score: Number(formState.readiness_score),
        }),
      })
      setFormState({
        apparatus_id: '',
        apparatus_type: '',
        status: 'In Service',
        mileage: 0,
        readiness_score: 100,
      })
      await loadApparatus()
    } catch (error) {
      console.warn('Unable to create apparatus', error)
    }
  }

  const createInventory = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/fire/apparatus/inventory', {
        method: 'POST',
        body: JSON.stringify({
          ...inventoryState,
          apparatus_id: Number(inventoryState.apparatus_id),
          quantity: Number(inventoryState.quantity),
        }),
      })
      await loadInventory(inventoryState.apparatus_id)
      setInventoryState({
        apparatus_id: inventoryState.apparatus_id,
        item_name: '',
        status: 'Ready',
        quantity: 1,
        notes: '',
      })
    } catch (error) {
      console.warn('Unable to create inventory item', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Apparatus & Inventory"
        title="Readiness, Maintenance, and Equipment"
        action={<button className="ghost-button">Fleet Report</button>}
      />

      <div className="section-grid">
        <div className="panel form-panel">
          <form className="form-grid" onSubmit={createApparatus}>
            <div>
              <label>Apparatus ID</label>
              <input
                name="apparatus_id"
                value={formState.apparatus_id}
                onChange={handleChange}
                placeholder="E-12"
                required
              />
            </div>
            <div>
              <label>Type</label>
              <input
                name="apparatus_type"
                value={formState.apparatus_type}
                onChange={handleChange}
                placeholder="Engine / Ladder / Rescue"
                required
              />
            </div>
            <div>
              <label>Status</label>
              <select name="status" value={formState.status} onChange={handleChange}>
                <option>In Service</option>
                <option>Out of Service</option>
                <option>Maintenance</option>
              </select>
            </div>
            <div>
              <label>Mileage</label>
              <input
                name="mileage"
                type="number"
                value={formState.mileage}
                onChange={handleChange}
              />
            </div>
            <div>
              <label>Readiness Score</label>
              <input
                name="readiness_score"
                type="number"
                value={formState.readiness_score}
                onChange={handleChange}
              />
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="submit">
                Add Apparatus
              </button>
            </div>
          </form>
        </div>
        <div className="panel form-panel">
          <SectionHeader eyebrow="Inventory" title="Linked Equipment" />
          <form className="form-grid" onSubmit={createInventory}>
            <div>
              <label>Apparatus ID</label>
              <input
                name="apparatus_id"
                value={inventoryState.apparatus_id}
                onChange={handleInventoryChange}
                placeholder="Select apparatus id"
                required
              />
            </div>
            <div>
              <label>Item</label>
              <input
                name="item_name"
                value={inventoryState.item_name}
                onChange={handleInventoryChange}
                placeholder="SCBA, AED, Hose"
                required
              />
            </div>
            <div>
              <label>Status</label>
              <select
                name="status"
                value={inventoryState.status}
                onChange={handleInventoryChange}
              >
                <option>Ready</option>
                <option>Needs Service</option>
                <option>Missing</option>
              </select>
            </div>
            <div>
              <label>Quantity</label>
              <input
                name="quantity"
                type="number"
                value={inventoryState.quantity}
                onChange={handleInventoryChange}
              />
            </div>
            <div className="full-width">
              <label>Notes</label>
              <input
                name="notes"
                value={inventoryState.notes}
                onChange={handleInventoryChange}
                placeholder="Inspection notes"
              />
            </div>
            <div className="full-width align-end">
              <button className="ghost-button" type="submit">
                Add Inventory Item
              </button>
            </div>
          </form>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Fleet" title="Apparatus Status" />
        <DataTable
          columns={apparatusColumns}
          rows={apparatusList}
          emptyState="No apparatus configured."
        />
      </div>

      <div className="panel">
        <SectionHeader
          eyebrow="Equipment"
          title="Inventory Items"
          action={
            <button
              className="ghost-button"
              type="button"
              onClick={() => loadInventory(inventoryState.apparatus_id)}
            >
              Refresh
            </button>
          }
        />
        <DataTable
          columns={inventoryColumns}
          rows={inventory}
          emptyState="No inventory items linked."
        />
      </div>
    </div>
  )
}
