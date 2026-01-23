import { useState } from 'react'
import { useParams } from 'react-router-dom'
import SectionHeader from '../components/SectionHeader.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import LegalHoldBanner from '../components/LegalHoldBanner.jsx'
import { apiFetch } from '../services/api.js'

export default function HemsClinical() {
  const { missionId } = useParams()
  const [formState, setFormState] = useState({
    vitals_trends: '{}',
    ventilator_settings: '{}',
    infusions: '[]',
    procedures: '[]',
    handoff_summary: '',
  })
  const [handoffState, setHandoffState] = useState({
    receiving_clinician: '',
    signature: '',
    notes: '',
  })

  const handleChange = (event) => {
    const { name, value } = event.target
    setFormState((prev) => ({ ...prev, [name]: value }))
  }

  const handleHandoffChange = (event) => {
    const { name, value } = event.target
    setHandoffState((prev) => ({ ...prev, [name]: value }))
  }

  const saveChart = async () => {
    try {
      await apiFetch(`/api/hems/missions/${missionId}/chart`, {
        method: 'POST',
        body: JSON.stringify({
          vitals_trends: JSON.parse(formState.vitals_trends || '{}'),
          ventilator_settings: JSON.parse(formState.ventilator_settings || '{}'),
          infusions: JSON.parse(formState.infusions || '[]'),
          procedures: JSON.parse(formState.procedures || '[]'),
          handoff_summary: formState.handoff_summary,
        }),
      })
    } catch (error) {
      console.warn('Unable to save chart', error)
    }
  }

  const saveHandoff = async () => {
    try {
      await apiFetch(`/api/hems/missions/${missionId}/handoff`, {
        method: 'POST',
        body: JSON.stringify(handoffState),
      })
      setHandoffState({ receiving_clinician: '', signature: '', notes: '' })
    } catch (error) {
      console.warn('Unable to save handoff', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="HEMS Clinical"
        title={`Critical Care Charting — Mission ${missionId}`}
        action={<button className="ghost-button">Print Draft</button>}
      />
      <LegalHoldBanner scopeType="hems_chart" scopeId={missionId || 'pending'} />

      <div className="section-grid">
        <div className="panel form-panel">
          <SectionHeader eyebrow="Chart" title="Vitals + Procedures" />
          <div className="form-grid">
            <div className="full-width">
              <label>Vitals Trends (JSON)</label>
              <textarea
                name="vitals_trends"
                value={formState.vitals_trends}
                onChange={handleChange}
              />
            </div>
            <div className="full-width">
              <label>Ventilator Settings (JSON)</label>
              <textarea
                name="ventilator_settings"
                value={formState.ventilator_settings}
                onChange={handleChange}
              />
            </div>
            <div className="full-width">
              <label>Infusions (JSON)</label>
              <textarea name="infusions" value={formState.infusions} onChange={handleChange} />
            </div>
            <div className="full-width">
              <label>Procedures (JSON)</label>
              <textarea name="procedures" value={formState.procedures} onChange={handleChange} />
            </div>
            <div className="full-width">
              <label>Handoff Summary</label>
              <textarea
                name="handoff_summary"
                value={formState.handoff_summary}
                onChange={handleChange}
              />
            </div>
            <div className="full-width align-end">
              <button className="primary-button" type="button" onClick={saveChart}>
                Save Chart
              </button>
            </div>
          </div>
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Clinical AI Advisory"
            model="quantum-ai"
            version="1.0"
            level="ADVISORY"
            message="Ventilator settings trending high. Confirm sedation protocol before handoff."
            reason="Realtime trend analysis on vent + infusion changes."
          />
          <div className="note-card">
            <p className="note-title">Protocol Checklist</p>
            <p className="note-body">
              Ensure airway confirmation, infusion tracking, and ECMO notes are complete.
            </p>
          </div>
        </div>
      </div>

      <div className="panel form-panel">
        <SectionHeader eyebrow="Handoff" title="Receiving Clinician Signoff" />
        <div className="form-grid">
          <div>
            <label>Receiving Clinician</label>
            <input
              name="receiving_clinician"
              value={handoffState.receiving_clinician}
              onChange={handleHandoffChange}
              placeholder="Dr. Chen"
            />
          </div>
          <div>
            <label>Signature</label>
            <input
              name="signature"
              value={handoffState.signature}
              onChange={handleHandoffChange}
              placeholder="Signature reference"
            />
          </div>
          <div className="full-width">
            <label>Notes</label>
            <textarea name="notes" value={handoffState.notes} onChange={handleHandoffChange} />
          </div>
          <div className="full-width align-end">
            <button className="primary-button" type="button" onClick={saveHandoff}>
              Submit Handoff
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
