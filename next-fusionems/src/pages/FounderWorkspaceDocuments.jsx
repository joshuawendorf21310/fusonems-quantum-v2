import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import { apiFetch } from '../services/api.js'
import { fallbackDocumentExports, fallbackDocumentFiles } from '../data/fallback.js'

const fileColumns = [
  { key: 'filename', label: 'File' },
  { key: 'classification', label: 'Class' },
  { key: 'status', label: 'Status' },
]

const exportColumns = [
  { key: 'id', label: 'Export' },
  { key: 'export_type', label: 'Type' },
  { key: 'status', label: 'Status' },
]

export default function FounderWorkspaceDocuments() {
  const [files, setFiles] = useState(fallbackDocumentFiles)
  const [exports, setExports] = useState(fallbackDocumentExports)

  useEffect(() => {
    const load = async () => {
      try {
        const [fileData, exportData] = await Promise.all([
          apiFetch('/api/documents/files'),
          apiFetch('/api/documents/exports/history'),
        ])
        if (Array.isArray(fileData) && fileData.length > 0) {
          setFiles(fileData)
        }
        if (Array.isArray(exportData) && exportData.length > 0) {
          setExports(exportData)
        }
      } catch (error) {
        // fallback remains
      }
    }
    load()
  }, [])

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Workspace" title="Documents Oversight" />
      <div className="panel">
        <SectionHeader eyebrow="Files" title="Vault Inventory" />
        <DataTable columns={fileColumns} rows={files} emptyState="No files yet." />
      </div>
      <div className="panel">
        <SectionHeader eyebrow="Exports" title="Discovery History" />
        <DataTable columns={exportColumns} rows={exports} emptyState="No exports yet." />
      </div>
    </div>
  )
}
