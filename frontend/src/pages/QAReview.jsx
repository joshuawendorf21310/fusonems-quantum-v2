import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import {
  fallbackQACases,
  fallbackQARubrics,
  fallbackQAReviews,
  fallbackRemediations,
} from '../data/fallback.js'

const caseColumns = [
  { key: 'linked_run_id', label: 'Run' },
  { key: 'case_type', label: 'Type' },
  { key: 'priority', label: 'Priority' },
  { key: 'status', label: 'Status' },
  { key: 'trigger', label: 'Trigger' },
]

const rubricColumns = [
  { key: 'name', label: 'Rubric' },
  { key: 'version', label: 'Version' },
  { key: 'status', label: 'Status' },
]

const reviewColumns = [
  { key: 'case_id', label: 'Case' },
  { key: 'reviewer', label: 'Reviewer' },
  { key: 'determination', label: 'Determination' },
  { key: 'summary', label: 'Summary' },
]

const remediationColumns = [
  { key: 'case_id', label: 'Case' },
  { key: 'plan', label: 'Plan' },
  { key: 'status', label: 'Status' },
]

export default function QAReview() {
  const [cases, setCases] = useState(fallbackQACases)
  const [rubrics, setRubrics] = useState(fallbackQARubrics)
  const [reviews, setReviews] = useState(fallbackQAReviews)
  const [remediations, setRemediations] = useState(fallbackRemediations)

  const loadQA = async () => {
    try {
      const [caseData, rubricData] = await Promise.all([
        apiFetch('/api/qa/cases'),
        apiFetch('/api/qa/rubrics'),
      ])
      if (Array.isArray(caseData) && caseData.length > 0) {
        setCases(caseData)
      }
      if (Array.isArray(rubricData) && rubricData.length > 0) {
        setRubrics(rubricData)
      }
    } catch (error) {
      console.warn('QA data unavailable', error)
    }
  }

  useEffect(() => {
    loadQA()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Clinical QA"
        title="Review Queue & Remediation"
        action={<button className="primary-button">Assign Case</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Queue" title="Active QA Cases" />
          <DataTable columns={caseColumns} rows={cases} emptyState="No QA cases yet." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Risk Scan"
            model="qa-assist"
            version="2.1"
            level="ADVISORY"
            message="3 airway cases flagged for protocol deviation in the last 72 hours."
            reason="QA rules + deviation triggers"
          />
          <div className="note-card">
            <p className="note-title">Remediation Watch</p>
            <p className="note-body">2 remediation plans open. 1 due within 24 hours.</p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Rubrics" title="Scoring Systems" />
        <DataTable columns={rubricColumns} rows={rubrics} emptyState="No rubrics yet." />
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Reviews" title="Recent Determinations" />
          <DataTable columns={reviewColumns} rows={reviews} emptyState="No reviews recorded." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Remediation" title="Active Plans" />
          <DataTable columns={remediationColumns} rows={remediations} emptyState="No remediation plans." />
        </div>
      </div>
    </div>
  )
}
