
import React, { useState } from "react"
import { DataGrid } from "react-data-grid"
import "react-data-grid/lib/styles.css"
import { FaSave, FaUndo, FaRedo, FaPlus, FaMinus } from "react-icons/fa"

interface Props {
  data: any[][]
  onChange: (data: any[][]) => void
}

const SpreadsheetEditor: React.FC<Props> = ({ data, onChange }) => {
  const [gridData, setGridData] = useState(data)
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    onChange(gridData)
    setSaving(false)
  }

  const toolbar = (
    <div className="flex items-center gap-2 p-2 rounded-t-lg border-b" style={{ background: "#217346", borderColor: "#1a5c38" }}>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Add Row"><FaPlus /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Remove Row"><FaMinus /></button>
      <span className="mx-2 border-l border-white/30 h-6" />
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Undo"><FaUndo /></button>
      <button className="p-2 hover:bg-white/20 rounded text-white" title="Redo"><FaRedo /></button>
      <span className="flex-1" />
      <button className="p-2 bg-white/20 text-white rounded flex items-center gap-1 hover:bg-white/30" onClick={handleSave} disabled={saving} title="Save">
        <FaSave /> {saving ? "Saving..." : "Save"}
      </button>
    </div>
  )

  const columns = (gridData[0] || []).map((_, i) => ({ key: String(i), name: i < 26 ? String.fromCharCode(65 + i) : `Col ${i + 1}` }))
  const rows = gridData.map((row, i) => ({ id: i, ...Object.fromEntries((row || []).map((v, j) => [String(j), v ?? ""])) }))

  return (
    <div className="bg-white rounded-lg shadow border max-w-5xl mx-auto" style={{ borderColor: "#EDEBE9" }}>
      {toolbar}
      <div className="p-4 bg-white rounded-b-lg min-h-[400px]">
        {columns.length > 0 ? (
          <DataGrid columns={columns} rows={rows} />
        ) : (
          <p className="text-gray-500 py-8">Empty spreadsheet. Add rows to get started.</p>
        )}
      </div>
    </div>
  )
}

export default SpreadsheetEditor
