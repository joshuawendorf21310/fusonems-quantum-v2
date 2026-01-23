import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackDocRecords, fallbackDocTemplates } from '../data/fallback.js'

const templateColumns = [
  { key: 'name', label: 'Template' },
  { key: 'module_key', label: 'Module' },
  { key: 'template_version', label: 'Version' },
  { key: 'status', label: 'Status' },
  { key: 'jurisdiction', label: 'Jurisdiction' },
]

const recordColumns = [
  { key: 'title', label: 'Document' },
  { key: 'output_format', label: 'Format' },
  { key: 'status', label: 'Status' },
  { key: 'document_hash', label: 'Hash' },
  { key: 'created_at', label: 'Created' },
]

export default function DocumentStudio() {
  const [templates, setTemplates] = useState(fallbackDocTemplates)
  const [records, setRecords] = useState(fallbackDocRecords)
  const [templateForm, setTemplateForm] = useState({
    name: '',
    module_key: 'EPCR',
    template_version: 'v1',
    status: 'draft',
    jurisdiction: 'default',
  })
  const [recordForm, setRecordForm] = useState({
    template_id: '',
    title: '',
    output_format: 'PDF',
  })

  const loadTemplates = async () => {
    try {
      const data = await apiFetch('/api/documents/templates')
      if (Array.isArray(data) && data.length > 0) {
        setTemplates(data)
      }
    } catch (error) {
      console.warn('Document templates unavailable', error)
    }
  }

  const loadRecords = async () => {
    try {
      const data = await apiFetch('/api/documents/records')
      if (Array.isArray(data) && data.length > 0) {
        setRecords(data)
      }
    } catch (error) {
      console.warn('Document records unavailable', error)
    }
  }

  useEffect(() => {
    loadTemplates()
    loadRecords()
  }, [])

  const handleTemplateChange = (event) => {
    const { name, value } = event.target
    setTemplateForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleRecordChange = (event) => {
    const { name, value } = event.target
    setRecordForm((prev) => ({ ...prev, [name]: value }))
  }

  const createTemplate = async (event) => {
    event.preventDefault()
    try {
      const created = await apiFetch('/api/documents/templates', {
        method: 'POST',
        body: JSON.stringify({ ...templateForm, sections: [] }),
      })
      setTemplates((prev) => [created, ...prev])
      setTemplateForm({ ...templateForm, name: '' })
    } catch (error) {
      console.warn('Unable to create template', error)
    }
  }

  const createRecord = async (event) => {
    event.preventDefault()
    if (!recordForm.template_id) {
      return
    }
    try {
      const created = await apiFetch('/api/documents/records', {
        method: 'POST',
        body: JSON.stringify({
          template_id: Number(recordForm.template_id),
          title: recordForm.title,
          output_format: recordForm.output_format,
          content: { summary: 'Generated from demo data' },
          provenance: { source: 'document_studio' },
        }),
      })
      setRecords((prev) => [created, ...prev])
      setRecordForm({ ...recordForm, title: '', template_id: '' })
    } catch (error) {
      console.warn('Unable to generate document', error)
    }
  }

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Document Studio"
        title="Legal-Grade Output Builder"
        action={<button className="primary-button">Generate Packet</button>}
      />

      <div className="section-grid">
        <div className="panel doc-studio-panel">
          <SectionHeader eyebrow="Templates" title="Versioned Templates" />
          <form className="form-grid" onSubmit={createTemplate}>
            <label className="field">
              <span>Name</span>
              <input name="name" value={templateForm.name} onChange={handleTemplateChange} required />
            </label>
            <label className="field">
              <span>Module</span>
              <select name="module_key" value={templateForm.module_key} onChange={handleTemplateChange}>
                <option value="EPCR">ePCR</option>
                <option value="HEMS">HEMS</option>
                <option value="BILLING">Billing</option>
                <option value="LEGAL_PORTAL">Legal</option>
              </select>
            </label>
            <label className="field">
              <span>Status</span>
              <select name="status" value={templateForm.status} onChange={handleTemplateChange}>
                <option value="draft">Draft</option>
                <option value="active">Active</option>
                <option value="deprecated">Deprecated</option>
              </select>
            </label>
            <label className="field">
              <span>Jurisdiction</span>
              <input name="jurisdiction" value={templateForm.jurisdiction} onChange={handleTemplateChange} />
            </label>
            <button className="ghost-button" type="submit">
              Save Template
            </button>
          </form>
          <DataTable columns={templateColumns} rows={templates} emptyState="No templates yet." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Provenance Guardrails"
            model="doc-engine"
            version="2.4"
            level="ADVISORY"
            message="Templates enforce jurisdiction-safe wording, legal hold banners, and hash-linked signatures."
            reason="Template registry + legal hold engine"
          />
          <div className="note-card">
            <p className="note-title">Generation Queue</p>
            <p className="note-body">2 packets queued for PDF + JSON bundles. Audit stamps included.</p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Records" title="Recent Document Outputs" />
        <form className="form-grid" onSubmit={createRecord}>
          <label className="field">
            <span>Template</span>
            <select name="template_id" value={recordForm.template_id} onChange={handleRecordChange} required>
              <option value="">Select template</option>
              {templates.map((template) => (
                <option key={template.id} value={template.id}>
                  {template.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span>Title</span>
            <input name="title" value={recordForm.title} onChange={handleRecordChange} required />
          </label>
          <label className="field">
            <span>Format</span>
            <select name="output_format" value={recordForm.output_format} onChange={handleRecordChange}>
              <option value="PDF">PDF</option>
              <option value="HTML">HTML</option>
              <option value="JSON">JSON</option>
            </select>
          </label>
          <button className="ghost-button" type="submit">
            Generate Document
          </button>
        </form>
        <DataTable columns={recordColumns} rows={records} emptyState="No document outputs yet." />
      </div>
    </div>
  )
}
