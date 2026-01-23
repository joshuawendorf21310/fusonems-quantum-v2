import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'

const personnelColumns = [
  { key: 'full_name', label: 'Name' },
  { key: 'role', label: 'Role' },
  { key: 'certifications', label: 'Certifications' },
  { key: 'status', label: 'Status' },
]

export default function FirePersonnel() {
  const [personnel, setPersonnel] = useState([])
  const [formState, setFormState] = useState({
    full_name: '',
    role: '',
    certifications: '',
  })

  const loadPersonnel = async () => {
    try {
      const data = await apiFetch('/api/fire/personnel')
      setPersonnel(data)
    } catch (error) {
      console.warn('Unable to load personnel', error)
    }
  }

  useEffect(() => {
    loadPersonnel()
  }, [])

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    try {
      await apiFetch('/api/fire/personnel', {
        method: 'POST',
        body: JSON.stringify(formState),
      })
      setFormState({ full_name: '', role: '', certifications: '' })
      await loadPersonnel()
    } catch (error) {
      console.warn('Unable to add personnel', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Personnel & Roles"
        title="Firefighter Profiles and Certifications"
        action={<button className="ghost-button">RBAC Summary</button>}
      />

      <div className="panel form-panel">
        <form className="form-grid" onSubmit={handleSubmit}>
          <div>
            <label>Name</label>
            <input
              name="full_name"
              value={formState.full_name}
              onChange={handleChange}
              placeholder="Alex Rivera"
              required
            />
          </div>
          <div>
            <label>Role</label>
            <input
              name="role"
              value={formState.role}
              onChange={handleChange}
              placeholder="Captain, Medic, Engineer"
              required
            />
          </div>
          <div className="full-width">
            <label>Certifications</label>
            <input
              name="certifications"
              value={formState.certifications}
              onChange={handleChange}
              placeholder="Firefighter II, EMT-P, Hazmat"
            />
          </div>
          <div className="full-width align-end">
            <button className="primary-button" type="submit">
              Add Personnel
            </button>
          </div>
        </form>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Roster" title="Active Personnel" />
        <DataTable
          columns={personnelColumns}
          rows={personnel}
          emptyState="No personnel records yet."
        />
      </div>
    </div>
  )
}
