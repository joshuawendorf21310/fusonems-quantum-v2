import { useEffect, useMemo, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'
import {
  fallbackDocumentExports,
  fallbackDocumentFiles,
  fallbackDocumentFolders,
} from '../data/fallback.js'

export default function Documents() {
  const [folders, setFolders] = useState(fallbackDocumentFolders)
  const [files, setFiles] = useState(fallbackDocumentFiles)
  const [exports, setExports] = useState(fallbackDocumentExports)
  const [activeFolder, setActiveFolder] = useState(null)
  const [activeFile, setActiveFile] = useState(null)
  const [search, setSearch] = useState('')
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    const load = async () => {
      try {
        const [folderData, fileData, exportData] = await Promise.all([
          apiFetch('/api/documents/folders'),
          apiFetch('/api/documents/files'),
          apiFetch('/api/documents/exports/history'),
        ])
        if (Array.isArray(folderData) && folderData.length > 0) {
          setFolders(folderData)
        }
        if (Array.isArray(fileData) && fileData.length > 0) {
          setFiles(fileData)
        }
        if (Array.isArray(exportData) && exportData.length > 0) {
          setExports(exportData)
        }
      } catch (error) {
        // Fallback data keeps the workspace alive.
      }
    }
    load()
  }, [])

  const filteredFiles = useMemo(() => {
    const byFolder = activeFolder ? files.filter((file) => file.folder_id === activeFolder) : files
    if (!search) {
      return byFolder
    }
    return byFolder.filter((file) => file.filename?.toLowerCase().includes(search.toLowerCase()))
  }, [files, activeFolder, search])

  const handleUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) {
      return
    }
    const formData = new FormData()
    formData.append('file', file)
    if (activeFolder) {
      formData.append('folder_id', activeFolder)
    }
    formData.append('classification', 'ops')
    formData.append('tags', JSON.stringify(['vault']))
    setUploading(true)
    try {
      const response = await fetch('/api/documents/files', {
        method: 'POST',
        credentials: 'include',
        body: formData,
      })
      if (response.ok) {
        const created = await response.json()
        setFiles((prev) => [created, ...prev])
      }
    } finally {
      setUploading(false)
    }
  }

  const fileColumns = [
    { key: 'filename', label: 'File' },
    { key: 'classification', label: 'Class' },
    {
      key: 'status',
      label: 'Status',
      render: (row) => <StatusBadge value={row.status || 'Open'} />,
    },
    {
      key: 'download',
      label: 'Download',
      render: (row) => (
        <a className="table-action" href={row.download_url || '#'} target="_blank" rel="noreferrer">
          Open
        </a>
      ),
    },
  ]

  const exportColumns = [
    { key: 'id', label: 'Export' },
    { key: 'export_type', label: 'Type' },
    { key: 'status', label: 'Status' },
    { key: 'created_at', label: 'Created' },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Quantum Documents"
        title="Drive + Vault"
        action={
          <label className="primary-button">
            {uploading ? 'Uploading…' : 'Upload'}
            <input type="file" onChange={handleUpload} hidden />
          </label>
        }
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Folders" title="Workspace Map" />
          <div className="note-stack">
            {folders.map((folder) => (
              <button
                key={folder.id}
                type="button"
                className={`note-card ${activeFolder === folder.id ? 'active' : ''}`}
                onClick={() => setActiveFolder(folder.id)}
              >
                <p className="note-title">{folder.name}</p>
                <p className="note-body">{folder.path_slug}</p>
              </button>
            ))}
          </div>
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Search" title="Find Documents" />
          <div className="search-input-row">
            <input
              className="text-input"
              placeholder="Search by filename"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
          </div>
          <AdvisoryPanel
            title="Vault Guidance"
            model="document-guard"
            version="2.0"
            level="ADVISORY"
            message="Retention policies enforce hold-safe deletion. Exports are hash-verified."
            reason="Quantum Vault rules"
          />
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Files" title="Recent Documents" />
        <DataTable columns={fileColumns} rows={filteredFiles} emptyState="No files yet." />
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Exports" title="Discovery Packets" />
        <DataTable columns={exportColumns} rows={exports} emptyState="No exports yet." />
      </div>
    </div>
  )
}
