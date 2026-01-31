"use client"

import React, { useState, useRef } from "react"
import dynamic from "next/dynamic"
import Link from "next/link"

const PDFViewer = dynamic(() => import("@/components/founder/PDFViewer"), { ssr: false })
const PDFEditor = dynamic(() => import("@/components/founder/PDFEditor"), { ssr: false })
const DocumentEditor = dynamic(() => import("@/components/founder/DocumentEditor"), { ssr: false })
const SpreadsheetEditor = dynamic(() => import("@/components/founder/SpreadsheetEditor"), { ssr: false })
const PresentationViewer = dynamic(() => import("@/components/founder/PresentationViewer"), { ssr: false })

// Office 365 colors
const WORD_BLUE = "#2B579A"
const EXCEL_GREEN = "#217346"
const POWERPOINT_ORANGE = "#D83B01"
const PDF_RED = "#E74C3C"
const BG_LIGHT = "#F3F2F1"
const BG_WHITE = "#FFFFFF"
const BORDER = "#EDEBE9"
const TEXT_PRIMARY = "#323130"
const TEXT_SECONDARY = "#605E5C"

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

function getDocKind(name: string, type: string): "word" | "sheet" | "slides" | "pdf" | "other" {
  const lower = (name || "").toLowerCase()
  const t = (type || "").toLowerCase()
  if (lower.endsWith(".pdf") || t.includes("pdf")) return "pdf"
  if (lower.endsWith(".docx") || lower.endsWith(".doc") || t.includes("word") || t.includes("document")) return "word"
  if (lower.endsWith(".xlsx") || lower.endsWith(".xls") || lower.endsWith(".csv") || t.includes("sheet") || t.includes("excel")) return "sheet"
  if (lower.endsWith(".pptx") || lower.endsWith(".ppt") || t.includes("presentation") || t.includes("powerpoint")) return "slides"
  return "other"
}

function FileIcon({ kind, className }: { kind: string; className?: string }) {
  const c = className || "w-8 h-8"
  if (kind === "word") return <div className={c} style={{ background: WORD_BLUE, borderRadius: 2 }} title="Word" />
  if (kind === "sheet") return <div className={c} style={{ background: EXCEL_GREEN, borderRadius: 2 }} title="Spreadsheet" />
  if (kind === "slides") return <div className={c} style={{ background: POWERPOINT_ORANGE, borderRadius: 2 }} title="Presentation" />
  if (kind === "pdf") return <div className={c} style={{ background: PDF_RED, borderRadius: 2 }} title="PDF" />
  return <div className={c} style={{ background: "#605E5C", borderRadius: 2 }} title="File" />
}

interface Props {
  documents: DocumentItem[]
  folders: FolderItem[]
  onUpload: (files: File[], folderId: number | null) => void
  onCreateFolder: (name: string, parentId: number | null) => void
  onMove: (docId: number, folderId: number | null) => void
  onTag: (docId: number, tags: string[]) => void
  onSaveDoc?: (docId: number, content: string) => Promise<void>
  onLoadContent?: (docId: number) => Promise<string>
}

export default function Office365Documents({
  documents,
  folders,
  onUpload,
  onCreateFolder,
  onMove,
  onTag,
  onSaveDoc,
  onLoadContent,
}: Props) {
  const [currentFolder, setCurrentFolder] = useState<number | null>(null)
  const [newFolderName, setNewFolderName] = useState("")
  const [openDoc, setOpenDoc] = useState<DocumentItem | null>(null)
  const [newDocType, setNewDocType] = useState<"word" | "sheet" | "slides" | null>(null)
  const [pdfMode, setPdfMode] = useState<"view" | "edit">("view")
  const [ribbonTab, setRibbonTab] = useState<"Home" | "Insert">("Home")
  const [wordDocContent, setWordDocContent] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const folderPath = (fid: number | null): FolderItem[] => {
    const path: FolderItem[] = []
    let folder = folders.find(f => f.id === fid)
    while (folder) {
      path.unshift(folder)
      folder = folders.find(f => f.id === folder!.parentId)
    }
    return path
  }

  const currentDocs = documents.filter(d => d.folderId === currentFolder)
  const currentFolders = folders.filter(f => f.parentId === currentFolder)
  const showEditor = openDoc || newDocType
  const docKind = openDoc ? getDocKind(openDoc.name, openDoc.type) : newDocType

  // Load Word doc content from backend (DigitalOcean Spaces) when opening an existing file
  useEffect(() => {
    if (!openDoc || docKind !== "word" || !onLoadContent) {
      setWordDocContent(null)
      return
    }
    let cancelled = false
    setWordDocContent("<p>Loading…</p>")
    onLoadContent(openDoc.id).then((content) => {
      if (!cancelled) setWordDocContent(content || "<p></p>")
    })
    return () => { cancelled = true }
  }, [openDoc?.id, docKind, onLoadContent])

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) onUpload(Array.from(e.target.files), currentFolder)
  }
  const handleCreateFolder = () => {
    if (newFolderName.trim()) {
      onCreateFolder(newFolderName.trim(), currentFolder)
      setNewFolderName("")
    }
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: BG_LIGHT }}>
      {/* Top bar - Office 365 style */}
      <header
        className="flex items-center h-14 px-4 shrink-0 border-b"
        style={{ background: BG_WHITE, borderColor: BORDER }}
      >
        <Link href="/founder" className="flex items-center gap-2 mr-6" style={{ color: TEXT_PRIMARY }}>
          <div className="w-8 h-8 rounded flex items-center justify-center" style={{ background: WORD_BLUE }}>
            <span className="text-white font-bold text-sm">F</span>
          </div>
          <span className="font-semibold">FusionEMS Documents</span>
        </Link>
        <div className="flex items-center gap-1">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="px-3 py-1.5 rounded text-sm font-medium hover:bg-black/5"
            style={{ color: TEXT_PRIMARY }}
          >
            Upload
          </button>
          <input type="file" multiple ref={fileInputRef} className="hidden" onChange={handleUpload} />
          <div className="relative group">
            <button
              className="px-3 py-1.5 rounded text-sm font-medium flex items-center gap-1 hover:bg-black/5"
              style={{ background: WORD_BLUE, color: "#fff" }}
            >
              New <span className="text-xs">▼</span>
            </button>
            <div
              className="absolute left-0 top-full mt-1 py-1 rounded shadow-lg z-50 min-w-[180px] hidden group-hover:block"
              style={{ background: BG_WHITE, border: `1px solid ${BORDER}` }}
            >
              <button
                onClick={() => { setNewDocType("word"); setOpenDoc(null); }}
                className="w-full px-4 py-2 text-left text-sm flex items-center gap-3 hover:bg-black/5"
                style={{ color: TEXT_PRIMARY }}
              >
                <FileIcon kind="word" className="w-6 h-6" /> Word document
              </button>
              <button
                onClick={() => { setNewDocType("sheet"); setOpenDoc(null); }}
                className="w-full px-4 py-2 text-left text-sm flex items-center gap-3 hover:bg-black/5"
                style={{ color: TEXT_PRIMARY }}
              >
                <FileIcon kind="sheet" className="w-6 h-6" /> Spreadsheet
              </button>
              <button
                onClick={() => { setNewDocType("slides"); setOpenDoc(null); }}
                className="w-full px-4 py-2 text-left text-sm flex items-center gap-3 hover:bg-black/5"
                style={{ color: TEXT_PRIMARY }}
              >
                <FileIcon kind="slides" className="w-6 h-6" /> Presentation
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="flex-1 flex min-h-0">
        {/* Left sidebar - OneDrive style */}
        <aside
          className="w-56 shrink-0 border-r py-3 flex flex-col"
          style={{ background: BG_WHITE, borderColor: BORDER }}
        >
          <button
            onClick={() => { setCurrentFolder(null); setOpenDoc(null); setNewDocType(null); }}
            className="px-4 py-2 text-left text-sm font-medium hover:bg-black/5 flex items-center gap-2"
            style={{ color: TEXT_PRIMARY }}
          >
            <span>📁</span> My Files
          </button>
          <div className="px-4 py-2 flex items-center gap-2 mt-2">
            <input
              type="text"
              placeholder="New folder"
              value={newFolderName}
              onChange={e => setNewFolderName(e.target.value)}
              className="flex-1 px-2 py-1 text-sm rounded border"
              style={{ borderColor: BORDER, color: TEXT_PRIMARY }}
            />
            <button
              onClick={handleCreateFolder}
              className="px-2 py-1 text-sm rounded font-medium"
              style={{ background: BG_LIGHT, color: TEXT_PRIMARY }}
            >
              +
            </button>
          </div>
          <div className="mt-2 px-2 text-xs" style={{ color: TEXT_SECONDARY }}>
            Path: /{folderPath(currentFolder).map(f => f.name).join("/")}
          </div>
          {currentFolders.map(folder => (
            <button
              key={folder.id}
              onClick={() => setCurrentFolder(folder.id)}
              className="px-4 py-2 text-left text-sm hover:bg-black/5 flex items-center gap-2"
              style={{ color: TEXT_PRIMARY }}
            >
              <span>📁</span> {folder.name}
            </button>
          ))}
          {currentFolder != null && (
            <button
              onClick={() => setCurrentFolder(folders.find(f => f.id === currentFolder)?.parentId ?? null)}
              className="px-4 py-2 text-left text-sm hover:bg-black/5"
              style={{ color: TEXT_SECONDARY }}
            >
              ← Up
            </button>
          )}
        </aside>

        {/* Main: file list or editor */}
        <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
          {!showEditor ? (
            <>
              <div className="px-4 py-2 border-b" style={{ background: BG_WHITE, borderColor: BORDER }}>
                <table className="w-full text-sm" style={{ color: TEXT_PRIMARY }}>
                  <thead>
                    <tr style={{ color: TEXT_SECONDARY }}>
                      <th className="text-left py-2 font-normal w-10"></th>
                      <th className="text-left py-2 font-normal">Name</th>
                      <th className="text-left py-2 font-normal">Modified</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentFolders.map(folder => (
                      <tr
                        key={folder.id}
                        className="border-b cursor-pointer hover:bg-black/5"
                        style={{ borderColor: BORDER }}
                        onClick={() => setCurrentFolder(folder.id)}
                      >
                        <td className="py-2 px-2"><span>📁</span></td>
                        <td className="py-2 font-medium">{folder.name}</td>
                        <td className="py-2">—</td>
                      </tr>
                    ))}
                    {currentDocs.map(doc => {
                      const kind = getDocKind(doc.name, doc.type)
                      const canOpen = kind !== "other"
                      return (
                        <tr
                          key={doc.id}
                          className={`border-b ${canOpen ? "cursor-pointer hover:bg-black/5" : ""}`}
                          style={{ borderColor: BORDER }}
                          onClick={() => canOpen && (setOpenDoc(doc), setNewDocType(null), setPdfMode("view"))}
                        >
                          <td className="py-2 px-2"><FileIcon kind={kind} className="w-6 h-6" /></td>
                          <td className="py-2 font-medium">{doc.name}</td>
                          <td className="py-2" style={{ color: TEXT_SECONDARY }}>{doc.created_at?.slice(0, 10)}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
                {currentDocs.length === 0 && currentFolders.length === 0 && (
                  <p className="py-8 text-center" style={{ color: TEXT_SECONDARY }}>No files in this folder. Upload or create a new document.</p>
                )}
              </div>
            </>
          ) : (
            <>
              {/* Ribbon - Office 365 style */}
              <div
                className="flex items-center gap-6 px-4 py-2 border-b shrink-0"
                style={{ background: BG_WHITE, borderColor: BORDER }}
              >
                <button
                  onClick={() => { setOpenDoc(null); setNewDocType(null); }}
                  className="text-sm font-medium hover:underline"
                  style={{ color: TEXT_PRIMARY }}
                >
                  ← Back to files
                </button>
                <div className="flex gap-1">
                  {(["Home", "Insert"] as const).map(tab => (
                    <button
                      key={tab}
                      onClick={() => setRibbonTab(tab)}
                      className={`px-3 py-1.5 text-sm rounded ${ribbonTab === tab ? "font-semibold" : ""}`}
                      style={{
                        color: TEXT_PRIMARY,
                        background: ribbonTab === tab ? BG_LIGHT : "transparent",
                      }}
                    >
                      {tab}
                    </button>
                  ))}
                </div>
                {openDoc && (
                  <span className="text-sm truncate flex-1" style={{ color: TEXT_SECONDARY }}>{openDoc.name}</span>
                )}
                {openDoc && docKind === "pdf" && (
                  <div className="flex gap-1">
                    <button
                      onClick={() => setPdfMode("view")}
                      className={`px-2 py-1 text-xs rounded ${pdfMode === "view" ? "font-semibold" : ""}`}
                      style={{ background: pdfMode === "view" ? BG_LIGHT : "transparent", color: TEXT_PRIMARY }}
                    >
                      View
                    </button>
                    <button
                      onClick={() => setPdfMode("edit")}
                      className={`px-2 py-1 text-xs rounded ${pdfMode === "edit" ? "font-semibold" : ""}`}
                      style={{ background: pdfMode === "edit" ? BG_LIGHT : "transparent", color: TEXT_PRIMARY }}
                    >
                      Edit
                    </button>
                  </div>
                )}
              </div>

              {/* Document canvas */}
              <div className="flex-1 overflow-auto p-4" style={{ background: BG_LIGHT }}>
                {docKind === "word" && (
                  <DocumentEditor
                    docId={openDoc?.id ?? 0}
                    initialContent={
                      newDocType ? "<p>New document</p>" : (wordDocContent ?? "<p>Loading…</p>")
                    }
                    onSave={async (content) => { if (onSaveDoc && openDoc) await onSaveDoc(openDoc.id, content); }}
                  />
                )}
                {docKind === "sheet" && (
                  <SpreadsheetEditor
                    data={[["A", "B", "C"], ["1", "2", "3"], ["", "", ""]]}
                    onChange={() => {}}
                  />
                )}
                {docKind === "slides" && (
                  <PresentationViewer slides={["<h2>Slide 1</h2><p>New presentation</p>", "<h2>Slide 2</h2><p>Add content here</p>"]} />
                )}
                {docKind === "pdf" && openDoc?.url && (
                  pdfMode === "edit" ? (
                    <PDFEditor fileUrl={openDoc.url} onSave={() => {}} />
                  ) : (
                    <PDFViewer fileUrl={openDoc.url} />
                  )
                )}
              </div>
            </>
          )}
        </main>
      </div>
    </div>
  )
}
