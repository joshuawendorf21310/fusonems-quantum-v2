import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function AutomationCompliance() {
  const [rules, setRules] = useState([])
  const [tasks, setTasks] = useState([])
  const [issues, setIssues] = useState([])
  const [alerts, setAlerts] = useState([])

  const loadData = async () => {
    try {
      const [rulesData, tasksData, issuesData, alertsData] = await Promise.all([
        apiFetch('/api/automation/rules'),
        apiFetch('/api/automation/tasks'),
        apiFetch('/api/validation/issues'),
        apiFetch('/api/compliance/alerts'),
      ])
      setRules(rulesData)
      setTasks(tasksData)
      setIssues(issuesData)
      setAlerts(alertsData)
    } catch (error) {
      console.warn('Unable to load automation/compliance data', error)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const ruleColumns = [
    { key: 'name', label: 'Rule' },
    { key: 'trigger', label: 'Trigger' },
    { key: 'action', label: 'Action' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const taskColumns = [
    { key: 'title', label: 'Task' },
    { key: 'owner', label: 'Owner' },
    { key: 'priority', label: 'Priority', render: (row) => <StatusBadge value={row.priority} /> },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const issueColumns = [
    { key: 'entity_type', label: 'Entity' },
    { key: 'entity_id', label: 'ID' },
    { key: 'issue', label: 'Issue' },
    { key: 'severity', label: 'Severity', render: (row) => <StatusBadge value={row.severity} /> },
  ]

  const alertColumns = [
    { key: 'category', label: 'Category' },
    { key: 'message', label: 'Alert' },
    { key: 'severity', label: 'Severity', render: (row) => <StatusBadge value={row.severity} /> },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Automation & Compliance"
        title="Workflow Automation, Validation, and Audit"
        action={<button className="ghost-button">Run Quality Scan</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Rules" title="Automation Rules" />
          <DataTable columns={ruleColumns} rows={rules} emptyState="No automation rules." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Tasks" title="Smart Task Assignments" />
          <DataTable columns={taskColumns} rows={tasks} emptyState="No workflow tasks." />
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Validation" title="Data Quality Issues" />
          <DataTable columns={issueColumns} rows={issues} emptyState="No validation issues." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Compliance" title="HIPAA Alerts" />
          <DataTable columns={alertColumns} rows={alerts} emptyState="No compliance alerts." />
        </div>
      </div>
    </div>
  )
}
