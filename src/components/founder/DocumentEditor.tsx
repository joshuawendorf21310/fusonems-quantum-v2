
import dynamic from "next/dynamic"
import React, { useState, useEffect } from "react"
import { FaBold, FaItalic, FaUnderline, FaAlignLeft, FaAlignCenter, FaAlignRight, FaUndo, FaRedo, FaSave } from "react-icons/fa"

const TiptapEditor = dynamic(() => import("@/components/shared/TiptapEditor"), { ssr: false })

interface Props {
  docId: number
  initialContent: string
  onSave: (content: string) => void
}

const DocumentEditor: React.FC<Props> = ({ docId, initialContent, onSave }) => {
  const [content, setContent] = useState(initialContent)
  const [saving, setSaving] = useState(false)
  const [editor, setEditor] = useState<any>(null)

  // Sync when content is loaded from backend (e.g. after opening a saved doc)
  useEffect(() => {
    setContent(initialContent)
  }, [initialContent])

  const handleSave = async () => {
    setSaving(true)
    await onSave(content)
    setSaving(false)
  }

  const toolbar = (
    <div className="flex items-center gap-2 p-2 rounded-t-lg border-b" style={{ background: "#2B579A", borderColor: "#1e3a6f" }}>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Bold" onClick={() => editor?.chain().focus().toggleBold().run()}><FaBold /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Italic" onClick={() => editor?.chain().focus().toggleItalic().run()}><FaItalic /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Underline" onClick={() => editor?.chain().focus().toggleUnderline?.().run()}><FaUnderline /></button>
      <span className="mx-2 border-l border-white/30 h-6" />
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Align Left" onClick={() => editor?.chain().focus().setTextAlign("left").run()}><FaAlignLeft /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Align Center" onClick={() => editor?.chain().focus().setTextAlign("center").run()}><FaAlignCenter /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Align Right" onClick={() => editor?.chain().focus().setTextAlign("right").run()}><FaAlignRight /></button>
      <span className="mx-2 border-l border-white/30 h-6" />
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Undo" onClick={() => editor?.chain().focus().undo().run()}><FaUndo /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Redo" onClick={() => editor?.chain().focus().redo().run()}><FaRedo /></button>
      <span className="flex-1" />
      <button className="p-2 bg-white/20 text-white rounded flex items-center gap-1 hover:bg-white/30" onClick={handleSave} disabled={saving} title="Save">
        <FaSave /> {saving ? "Saving..." : "Save"}
      </button>
    </div>
  )

  return (
    <div className="bg-white rounded-lg shadow border max-w-4xl mx-auto" style={{ borderColor: "#EDEBE9" }}>
      {toolbar}
      <div className="p-6 min-h-[500px] bg-white rounded-b-lg">
        <TiptapEditor value={content} onChange={setContent} setEditor={setEditor} />
      </div>
    </div>
  )
}

export default DocumentEditor
