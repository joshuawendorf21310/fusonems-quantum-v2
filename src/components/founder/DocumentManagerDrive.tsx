import React, { useState, useRef } from "react"

interface DocumentItem {
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

interface Props {
  documents: DocumentItem[]
  folders: FolderItem[]
  onUpload: (files: File[], folderId: number | null) => void
  onCreateFolder: (name: string, parentId: number | null) => void
  onMove: (docId: number, folderId: number | null) => void
  onTag: (docId: number, tags: string[]) => void
}

const DocumentManagerDrive: React.FC<Props> = ({
  documents,
  folders,
  onUpload,
  onCreateFolder,
  onMove,
  onTag,
}) => {
  const [currentFolder, setCurrentFolder] = useState<number | null>(null)
  const [newFolderName, setNewFolderName] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      onUpload(Array.from(e.target.files), currentFolder)
    }
  }

  const handleCreateFolder = () => {
    if (newFolderName.trim()) {
      onCreateFolder(newFolderName.trim(), currentFolder)
      setNewFolderName("")
    }
  }

  const folderPath = (fid: number | null): FolderItem[] => {
    const path: FolderItem[] = []
    let folder = folders.find(f => f.id === fid)
    while (folder) {
      path.unshift(folder)
      folder = folders.find(f => f.id === folder.parentId)
    }
    return path
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4 shadow-lg">
      <div className="flex items-center mb-4">
        <button
          className="bg-blue-600 text-white px-3 py-1 rounded mr-2"
          onClick={() => fileInputRef.current?.click()}
        >
          Upload
        </button>
        <input
          type="file"
          multiple
          ref={fileInputRef}
          className="hidden"
          onChange={handleUpload}
        />
        <input
          type="text"
          placeholder="New folder name"
          value={newFolderName}
          onChange={e => setNewFolderName(e.target.value)}
          className="bg-gray-800 text-white px-2 py-1 rounded mr-2"
        />
        <button
          className="bg-green-600 text-white px-3 py-1 rounded"
          onClick={handleCreateFolder}
        >
          Create Folder
        </button>
      </div>
      <div className="mb-2 text-gray-400">
        Path: <span className="text-white">/
          {folderPath(currentFolder).map(f => (
            <span key={f.id}>
              {f.name}/
            </span>
          ))}
        </span>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {folders.filter(f => f.parentId === currentFolder).map(folder => (
          <div
            key={folder.id}
            className="bg-gray-800 rounded p-3 cursor-pointer hover:bg-gray-700"
            onClick={() => setCurrentFolder(folder.id)}
          >
            <div className="font-bold text-blue-400">📁 {folder.name}</div>
          </div>
        ))}
        {documents.filter(d => d.folderId === currentFolder).map(doc => (
          <div key={doc.id} className="bg-gray-800 rounded p-3">
            <div className="font-bold text-white">{doc.name}</div>
            <div className="text-xs text-gray-400">{doc.type}</div>
            <div className="text-xs text-gray-400">{doc.tags?.join(", ")}</div>
            <a
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:underline text-xs"
            >
              View
            </a>
          </div>
        ))}
      </div>
      {currentFolder && (
        <button
          className="mt-4 text-gray-400 hover:text-white"
          onClick={() => setCurrentFolder(folders.find(f => f.id === currentFolder)?.parentId ?? null)}
        >
          ← Up
        </button>
      )}
    </div>
  )
}

export default DocumentManagerDrive
