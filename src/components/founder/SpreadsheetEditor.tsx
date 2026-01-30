
import React, { useState } from "react"
import DataGrid from "react-data-grid"
import { FaSave, FaUndo, FaRedo, FaPlus, FaMinus, FaTable } from "react-icons/fa"

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

  // Office-like toolbar
  const toolbar = (
    <div className="flex items-center gap-2 bg-gradient-to-r from-green-900 to-green-700 p-2 rounded-t-lg border-b border-green-800 shadow">
      <button className="p-2 hover:bg-green-800 rounded" title="Add Row"><FaPlus /></button>
      <button className="p-2 hover:bg-green-800 rounded" title="Remove Row"><FaMinus /></button>
      <span className="mx-2 border-l border-green-400 h-6" />
      <button className="p-2 hover:bg-green-800 rounded" title="Undo"><FaUndo /></button>
      <button className="p-2 hover:bg-green-800 rounded" title="Redo"><FaRedo /></button>
      <span className="flex-1" />
      <button className="p-2 bg-green-600 text-white rounded flex items-center gap-1" onClick={handleSave} disabled={saving} title="Save">
        <FaSave /> {saving ? "Saving..." : "Save"}
      </button>
    </div>
  )

  return (
    <div className="bg-gradient-to-br from-green-950 to-green-900 rounded-lg shadow-2xl border border-green-800 max-w-5xl mx-auto mt-8">
      {toolbar}
      <div className="p-6 bg-white rounded-b-lg">
        <DataGrid columns={gridData[0].map((_, i) => ({ key: String(i), name: String(i) }))} rows={gridData.map((row, i) => ({ id: i, ...row }))} />
      </div>
    </div>
  )
}

export default SpreadsheetEditor
