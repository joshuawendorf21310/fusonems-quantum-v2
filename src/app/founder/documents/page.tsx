
"use client"

import { useEffect, useState } from "react"
import Office365Documents from "@/components/founder/Office365Documents"
import { apiClient, apiFetch } from "@/lib/api"

const API_DOCS = "/api/founder/documents"

interface DocumentRecord {
  id: number
  name: string
  type: string
  url: string
  tags?: string[]
  folderId?: number | null
  created_at: string
}

interface FolderItem {
  id: number
  name: string
  parentId?: number | null
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [folders, setFolders] = useState<FolderItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    fetchAll()
  }, [])

  const fetchAll = async () => {
    setLoading(true)
    setError("")
    try {
      const [docs, fols] = await Promise.all([
        apiFetch<DocumentRecord[]>(`${API_DOCS}/records`),
        apiFetch<FolderItem[]>(`${API_DOCS}/folders`),
      ])
      setDocuments(docs)
      setFolders(fols)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (files: File[], folderId: number | null) => {
    const formData = new FormData()
    formData.append("file", files[0])
    if (folderId != null) formData.append("folder_id", String(folderId))
    try {
      await apiClient.post(`${API_DOCS}/upload`, formData)
      await fetchAll()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Upload error")
    }
  }

  const handleCreateFolder = async (name: string, parentId: number | null) => {
    const formData = new FormData()
    formData.append("name", name)
    if (parentId != null) formData.append("parent_id", String(parentId))
    try {
      await apiClient.post(`${API_DOCS}/folders`, formData)
      await fetchAll()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Create folder error")
    }
  }

  const handleMove = async (docId: number, folderId: number | null) => {
    const formData = new FormData()
    if (folderId != null) formData.append("folder_id", String(folderId))
    try {
      await apiClient.post(`${API_DOCS}/files/${docId}/move`, formData)
      await fetchAll()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Move document error")
    }
  }

  const handleTag = async (docId: number, tags: string[]) => {
    const formData = new FormData()
    formData.append("tags", JSON.stringify(tags))
    try {
      await apiClient.post(`${API_DOCS}/files/${docId}/tag`, formData)
      await fetchAll()
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Tag update error")
    }
  }

  const handleSaveDoc = async (docId: number, content: string) => {
    try {
      await apiClient.put(`${API_DOCS}/files/${docId}/content`, { content })
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Save error")
    }
  }

  const loadContent = async (docId: number): Promise<string> => {
    try {
      const res = await apiFetch<{ content: string }>(`${API_DOCS}/files/${docId}/content`)
      return res?.content ?? ""
    } catch {
      return ""
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F3F2F1]">
        <p className="text-[#605E5C]">Loading documents…</p>
      </div>
    )
  }
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F3F2F1]">
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    )
  }

  return (
    <Office365Documents
      documents={documents}
      folders={folders}
      onUpload={handleUpload}
      onCreateFolder={handleCreateFolder}
      onMove={handleMove}
      onTag={handleTag}
      onSaveDoc={handleSaveDoc}
      onLoadContent={loadContent}
    />
  )
}
