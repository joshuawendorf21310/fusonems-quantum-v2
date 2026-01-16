import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackJobs } from '../data/fallback.js'

const jobColumns = [
  { key: 'job_type', label: 'Job Type' },
  { key: 'status', label: 'Status' },
  { key: 'attempts', label: 'Attempts' },
  { key: 'scheduled_for', label: 'Scheduled' },
]

export default function JobsConsole() {
  const [jobs, setJobs] = useState(fallbackJobs)

  const loadJobs = async () => {
    try {
      const data = await apiFetch('/api/jobs')
      if (Array.isArray(data) && data.length > 0) {
        setJobs(data)
      }
    } catch (error) {
      console.warn('Jobs queue unavailable', error)
    }
  }

  const runJob = async (jobId) => {
    try {
      await apiFetch(`/api/jobs/${jobId}/run`, { method: 'POST' })
      await loadJobs()
    } catch (error) {
      console.warn('Unable to run job', error)
    }
  }

  useEffect(() => {
    loadJobs()
  }, [])

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Background Jobs"
        title="Queue, Orchestration, Health"
        action={<button className="primary-button">Dispatch Worker</button>}
      />

      <div className="section-grid">
        <div className="panel jobs-panel">
          <SectionHeader eyebrow="Queue" title="Active Jobs" />
          <DataTable columns={jobColumns} rows={jobs} emptyState="No queued jobs." />
          <div className="panel-actions">
            {jobs.map((job) => (
              <button key={job.id} className="ghost-button" onClick={() => runJob(job.id)}>
                Run {job.job_type}
              </button>
            ))}
          </div>
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Queue Health"
            model="queue-monitor"
            version="1.3"
            level="ADVISORY"
            message="All workers connected. 0 failed jobs in the last hour."
            reason="Worker heartbeat + retry policy"
          />
          <div className="note-card">
            <p className="note-title">Degraded Mode</p>
            <p className="note-body">If queue depth exceeds 50, exports pause and founders are alerted.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
