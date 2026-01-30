import React, { useRef, useState } from "react"
import { Document, Page, pdfjs } from "react-pdf"
import { FaPen, FaHighlighter, FaSignature, FaSave, FaEraser, FaUndo, FaRedo } from "react-icons/fa"
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`

interface Props {
  fileUrl: string
  onSave: (blob: Blob) => void
}

const PDFEditor: React.FC<Props> = ({ fileUrl, onSave }) => {
  const [page, setPage] = useState(1)
  const [numPages, setNumPages] = useState<number | null>(null)
  // For demo: annotation state is not persisted; production would use a PDF annotation library
  const [tool, setTool] = useState<'pen' | 'highlight' | 'sign' | 'erase' | null>(null)
  const [saving, setSaving] = useState(false)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const handleSave = async () => {
    setSaving(true)
    // In production, export the annotated PDF as a Blob
    // For demo, just export the canvas as an image
    if (canvasRef.current) {
      canvasRef.current.toBlob(blob => {
        if (blob) onSave(blob)
        setSaving(false)
      })
    }
  }

  return (
    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-lg shadow-2xl border border-gray-700 max-w-3xl mx-auto mt-8">
      <div className="flex items-center gap-2 bg-gradient-to-r from-purple-900 to-purple-700 p-2 rounded-t-lg border-b border-purple-800 shadow">
        <span className="text-white font-bold">PDF Editor</span>
        <span className="flex-1" />
        <button className={`p-2 rounded ${tool === 'pen' ? 'bg-purple-600' : 'hover:bg-purple-800'}`} title="Pen" onClick={() => setTool('pen')}><FaPen /></button>
        <button className={`p-2 rounded ${tool === 'highlight' ? 'bg-purple-600' : 'hover:bg-purple-800'}`} title="Highlight" onClick={() => setTool('highlight')}><FaHighlighter /></button>
        <button className={`p-2 rounded ${tool === 'sign' ? 'bg-purple-600' : 'hover:bg-purple-800'}`} title="Sign" onClick={() => setTool('sign')}><FaSignature /></button>
        <button className={`p-2 rounded ${tool === 'erase' ? 'bg-purple-600' : 'hover:bg-purple-800'}`} title="Erase" onClick={() => setTool('erase')}><FaEraser /></button>
        <button className="p-2 bg-purple-600 text-white rounded flex items-center gap-1 ml-2" onClick={handleSave} disabled={saving} title="Save">
          <FaSave /> {saving ? "Saving..." : "Save"}
        </button>
      </div>
      <div className="p-6 bg-white rounded-b-lg flex flex-col items-center">
        <Document file={fileUrl} onLoadSuccess={({ numPages }) => setNumPages(numPages)}>
          <Page pageNumber={page} />
        </Document>
        <canvas ref={canvasRef} width={600} height={800} className="border mt-4" style={{ display: 'none' }} />
        <div className="mt-4 flex gap-2 items-center">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="bg-gray-700 text-white px-3 py-1 rounded">Prev</button>
          <span className="text-gray-700">Page {page} / {numPages}</span>
          <button disabled={numPages ? page >= numPages : true} onClick={() => setPage(p => p + 1)} className="bg-blue-700 text-white px-3 py-1 rounded">Next</button>
        </div>
      </div>
    </div>
  )
}

export default PDFEditor
