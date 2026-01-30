
import React, { useState } from "react"
import { Document, Page, pdfjs } from "react-pdf"
import { FaPrint, FaSearchMinus, FaSearchPlus, FaFilePdf } from "react-icons/fa"
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`

interface Props {
  fileUrl: string
}

const PDFViewer: React.FC<Props> = ({ fileUrl }) => {
  const [page, setPage] = useState(1)
  const [numPages, setNumPages] = useState<number | null>(null)
  const [scale, setScale] = useState(1.0)

  return (
    <div className="bg-white rounded-lg shadow border max-w-3xl mx-auto" style={{ borderColor: "#EDEBE9" }}>
      <div className="flex items-center gap-2 p-2 rounded-t-lg border-b" style={{ background: "#E74C3C", borderColor: "#c0392b" }}>
        <FaFilePdf className="text-white/90 mr-2" />
        <span className="text-white font-bold">PDF Viewer</span>
        <span className="flex-1" />
        <button className="p-2 hover:bg-white/20 rounded text-white" title="Zoom Out" onClick={() => setScale(s => Math.max(0.5, s - 0.1))}><FaSearchMinus /></button>
        <button className="p-2 hover:bg-white/20 rounded text-white" title="Zoom In" onClick={() => setScale(s => Math.min(2, s + 0.1))}><FaSearchPlus /></button>
        <button className="p-2 hover:bg-white/20 rounded text-white" title="Print" onClick={() => window.print()}><FaPrint /></button>
      </div>
      <div className="p-6 bg-white rounded-b-lg flex flex-col items-center">
        <Document file={fileUrl} onLoadSuccess={({ numPages }) => setNumPages(numPages)}>
          <Page pageNumber={page} scale={scale} />
        </Document>
        <div className="mt-4 flex gap-2 items-center">
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} className="bg-gray-700 text-white px-3 py-1 rounded">Prev</button>
          <span className="text-gray-700">Page {page} / {numPages}</span>
          <button disabled={numPages ? page >= numPages : true} onClick={() => setPage(p => p + 1)} className="bg-blue-700 text-white px-3 py-1 rounded">Next</button>
        </div>
      </div>
    </div>
  )
}

export default PDFViewer
