"use client";
import React, { useState } from "react"

interface PersonalTaxData {
  filingStatus: string
  income: number
  deductions: number
  dependents: number
  otherIncome: number
  notes: string
}

const defaultData: PersonalTaxData = {
  filingStatus: "single",
  income: 0,
  deductions: 0,
  dependents: 0,
  otherIncome: 0,
  notes: ""
}

const filingOptions = [
  { value: "single", label: "Single" },
  { value: "married_joint", label: "Married Filing Jointly" },
  { value: "married_separate", label: "Married Filing Separately" },
  { value: "head_household", label: "Head of Household" },
  { value: "qualifying_widow", label: "Qualifying Widow(er)" }
]

export default function PersonalTaxForm({ onSubmit }: { onSubmit: (data: PersonalTaxData) => void }) {
  const [form, setForm] = useState<PersonalTaxData>(defaultData)
  const [submitting, setSubmitting] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target
    setForm(f => ({ ...f, [name]: name === "income" || name === "deductions" || name === "dependents" || name === "otherIncome" ? Number(value) : value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)
    onSubmit(form)
    setSubmitting(false)
  }

  return (
    <form className="bg-white rounded-lg shadow-xl p-8 max-w-xl mx-auto border border-blue-200" onSubmit={handleSubmit}>
      <h2 className="text-2xl font-bold text-blue-900 mb-6">Personal Tax Information</h2>
      <div className="mb-4">
        <label className="block text-blue-800 font-semibold mb-1">Filing Status</label>
        <select name="filingStatus" value={form.filingStatus} onChange={handleChange} className="w-full border rounded px-3 py-2">
          {filingOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
        </select>
      </div>
      <div className="mb-4">
        <label className="block text-blue-800 font-semibold mb-1">Total Income ($)</label>
        <input type="number" name="income" value={form.income} onChange={handleChange} className="w-full border rounded px-3 py-2" min={0} />
      </div>
      <div className="mb-4">
        <label className="block text-blue-800 font-semibold mb-1">Deductions ($)</label>
        <input type="number" name="deductions" value={form.deductions} onChange={handleChange} className="w-full border rounded px-3 py-2" min={0} />
      </div>
      <div className="mb-4">
        <label className="block text-blue-800 font-semibold mb-1">Dependents</label>
        <input type="number" name="dependents" value={form.dependents} onChange={handleChange} className="w-full border rounded px-3 py-2" min={0} />
      </div>
      <div className="mb-4">
        <label className="block text-blue-800 font-semibold mb-1">Other Income ($)</label>
        <input type="number" name="otherIncome" value={form.otherIncome} onChange={handleChange} className="w-full border rounded px-3 py-2" min={0} />
      </div>
      <div className="mb-4">
        <label className="block text-blue-800 font-semibold mb-1">Notes</label>
        <textarea name="notes" value={form.notes} onChange={handleChange} className="w-full border rounded px-3 py-2" rows={3} />
      </div>
      <button type="submit" className="bg-blue-700 text-white px-6 py-2 rounded font-bold shadow hover:bg-blue-800" disabled={submitting}>
        {submitting ? "Saving..." : "Save & Continue"}
      </button>
    </form>
  )
}
