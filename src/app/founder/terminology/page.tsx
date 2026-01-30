"use client"

import Link from "next/link"
import { useCallback, useEffect, useState } from "react"
import Sidebar from "@/components/layout/Sidebar"
import Topbar from "@/components/layout/Topbar"
import { apiClient, apiFetch } from "@/lib/api"

const API = "/api/founder/terminology"

type TerminologyEntry = {
  id: number
  code_set: string
  use_case: string
  code: string
  description: string
  alternate_text: string | null
  nemsis_element_ref: string | null
  nemsis_value_set: string | null
  active: boolean
  sort_order: number
}

type SuggestResult = { code: string; description: string; nemsis_element_ref?: string | null }

const CODE_SETS = [
  { value: "icd10", label: "ICD-10", sub: "Diagnosis, impression, medication history", color: "orange", icon: "📋" },
  { value: "snomed", label: "SNOMED", sub: "Interventions", color: "cyan", icon: "🩺" },
  { value: "rxnorm", label: "RXNorm", sub: "Medications", color: "emerald", icon: "💊" },
] as const

const USE_CASES_ICD10 = [
  { value: "diagnosis", label: "Diagnosis / Chief complaint" },
  { value: "impression", label: "Clinical impression" },
  { value: "medication_history", label: "Medication history condition" },
]

export default function FounderTerminologyPage() {
  const [entries, setEntries] = useState<TerminologyEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [codeSetFilter, setCodeSetFilter] = useState<string>("")
  const [useCaseFilter, setUseCaseFilter] = useState<string>("")
  const [showForm, setShowForm] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState({
    code_set: "icd10",
    use_case: "diagnosis",
    code: "",
    description: "",
    alternate_text: "",
    nemsis_element_ref: "",
    nemsis_value_set: "",
    active: true,
    sort_order: 0,
  })
  const [aiQuery, setAiQuery] = useState("")
  const [aiLoading, setAiLoading] = useState(false)
  const [aiSuggestions, setAiSuggestions] = useState<SuggestResult[]>([])
  const [aiExplanation, setAiExplanation] = useState<string | null>(null)
  const [aiAvailable, setAiAvailable] = useState(false)

  const fetchEntries = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      const params = new URLSearchParams()
      if (codeSetFilter) params.set("code_set", codeSetFilter)
      if (useCaseFilter) params.set("use_case", useCaseFilter)
      params.set("active_only", "false")
      const data = await apiFetch<TerminologyEntry[]>(`${API}?${params}`)
      setEntries(Array.isArray(data) ? data : [])
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load terminology")
      setEntries([])
    } finally {
      setLoading(false)
    }
  }, [codeSetFilter, useCaseFilter])

  useEffect(() => {
    fetchEntries()
  }, [fetchEntries])

  const handleAiSuggest = async () => {
    if (!aiQuery.trim()) return
    setAiLoading(true)
    setAiSuggestions([])
    setAiExplanation(null)
    try {
      const res = await apiClient.post<{ suggestions: SuggestResult[]; explanation?: string; ai_available: boolean }>(
        `${API}/suggest`,
        { query: aiQuery.trim(), code_set: form.code_set }
      )
      setAiSuggestions(res.data.suggestions || [])
      setAiExplanation(res.data.explanation ?? null)
      setAiAvailable(res.data.ai_available ?? false)
    } catch (e) {
      setAiExplanation(e instanceof Error ? e.message : "AI suggest failed")
    } finally {
      setAiLoading(false)
    }
  }

  const applySuggestion = (s: SuggestResult) => {
    setForm((f) => ({ ...f, code: s.code, description: s.description }))
    setShowForm(true)
    setEditingId(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    try {
      if (editingId) {
        await apiClient.patch(`${API}/${editingId}`, {
          description: form.description || undefined,
          alternate_text: form.alternate_text || undefined,
          nemsis_element_ref: form.nemsis_element_ref || undefined,
          nemsis_value_set: form.nemsis_value_set || undefined,
          active: form.active,
          sort_order: form.sort_order,
        })
      } else {
        await apiClient.post(API, {
          code_set: form.code_set,
          use_case: form.use_case,
          code: form.code.trim(),
          description: form.description.trim(),
          alternate_text: form.alternate_text.trim() || undefined,
          nemsis_element_ref: form.nemsis_element_ref.trim() || undefined,
          nemsis_value_set: form.nemsis_value_set.trim() || undefined,
          active: form.active,
          sort_order: form.sort_order,
        })
      }
      setShowForm(false)
      setEditingId(null)
      setForm({
        code_set: "icd10",
        use_case: "diagnosis",
        code: "",
        description: "",
        alternate_text: "",
        nemsis_element_ref: "",
        nemsis_value_set: "",
        active: true,
        sort_order: 0,
      })
      await fetchEntries()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed")
    }
  }

  const handleEdit = (entry: TerminologyEntry) => {
    setEditingId(entry.id)
    setForm({
      code_set: entry.code_set,
      use_case: entry.use_case,
      code: entry.code,
      description: entry.description,
      alternate_text: entry.alternate_text ?? "",
      nemsis_element_ref: entry.nemsis_element_ref ?? "",
      nemsis_value_set: entry.nemsis_value_set ?? "",
      active: entry.active,
      sort_order: entry.sort_order,
    })
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (!confirm("Remove this terminology entry?")) return
    try {
      await apiClient.delete(`${API}/${id}`)
      await fetchEntries()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed")
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a]">
      <Sidebar />
      <main className="ml-64">
        <Topbar />
        <div className="p-8 max-w-7xl mx-auto">
          {/* Hero */}
          <header className="relative rounded-2xl overflow-hidden mb-8">
            <div className="absolute inset-0 bg-gradient-to-br from-orange-600/20 via-charcoal-900 to-cyan-600/10" />
            <div className="relative px-8 py-10">
              <p className="text-orange-400 text-sm font-medium uppercase tracking-wider">Founder</p>
              <h1 className="text-3xl md:text-4xl font-bold text-white mt-1">Terminology Builder</h1>
              <p className="text-zinc-400 mt-2 text-lg max-w-2xl">
                NEMSIS-constrained ICD-10, SNOMED, and RXNorm. Add or adjust codes for ePCR and billing. Use AI to suggest codes from free text.
              </p>
              <Link
                href="/founder"
                className="inline-flex items-center gap-2 mt-4 text-orange-400 hover:text-orange-300 font-medium"
              >
                ← Back to Founder Console
              </Link>
            </div>
          </header>

          {error && (
            <div className="mb-6 p-4 rounded-xl bg-red-900/30 border border-red-800/50 text-red-200 text-sm">
              {error}
            </div>
          )}

          {/* AI Suggest panel */}
          <section className="mb-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-2xl">✨</span>
              <h2 className="text-xl font-semibold text-white">AI suggest codes</h2>
            </div>
            <p className="text-zinc-400 text-sm mb-4">
              Describe a chief complaint or concept (e.g. &quot;chest pain&quot;, &quot;IV access&quot;) and get suggested codes to add.
            </p>
            <div className="flex flex-wrap gap-3">
              <select
                value={form.code_set}
                onChange={(e) => setForm((f) => ({ ...f, code_set: e.target.value }))}
                className="bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5 text-sm"
              >
                {CODE_SETS.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
              <input
                type="text"
                value={aiQuery}
                onChange={(e) => setAiQuery(e.target.value)}
                placeholder="e.g. chest pain, difficulty breathing"
                className="flex-1 min-w-[200px] bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5 placeholder-zinc-500"
              />
              <button
                type="button"
                onClick={handleAiSuggest}
                disabled={aiLoading || !aiQuery.trim()}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-500 hover:to-orange-400 text-white font-medium disabled:opacity-50 disabled:pointer-events-none"
              >
                {aiLoading ? "Thinking…" : "Suggest"}
              </button>
            </div>
            {aiExplanation && (
              <p className="mt-3 text-zinc-500 text-sm">{aiExplanation}</p>
            )}
            {aiSuggestions.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                {aiSuggestions.map((s, i) => (
                  <button
                    key={i}
                    type="button"
                    onClick={() => applySuggestion(s)}
                    className="px-4 py-2 rounded-xl bg-zinc-800/80 border border-zinc-600 hover:border-orange-500/50 hover:bg-zinc-700/80 text-left"
                  >
                    <span className="font-mono text-orange-400">{s.code}</span>
                    <span className="text-zinc-300 ml-2">{s.description}</span>
                  </button>
                ))}
              </div>
            )}
          </section>

          {/* Code set filter cards */}
          <div className="flex flex-wrap gap-4 mb-6">
            <span className="text-zinc-400 text-sm self-center">Filter:</span>
            {CODE_SETS.map(({ value, label, sub, icon }) => (
              <button
                key={value}
                type="button"
                onClick={() => setCodeSetFilter(codeSetFilter === value ? "" : value)}
                className={`px-5 py-2.5 rounded-xl border text-sm font-medium transition-all ${
                  codeSetFilter === value
                    ? "bg-orange-600/20 border-orange-500/50 text-orange-400"
                    : "bg-zinc-800/50 border-zinc-700 text-zinc-400 hover:border-zinc-600 hover:text-zinc-300"
                }`}
              >
                <span className="mr-2">{icon}</span>
                {label}
              </button>
            ))}
            {codeSetFilter === "icd10" && (
              <select
                value={useCaseFilter}
                onChange={(e) => setUseCaseFilter(e.target.value)}
                className="bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5 text-sm"
              >
                <option value="">All use cases</option>
                {USE_CASES_ICD10.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            )}
            <button
              type="button"
              onClick={() => {
                setShowForm(true)
                setEditingId(null)
                setForm({
                  code_set: "icd10",
                  use_case: "diagnosis",
                  code: "",
                  description: "",
                  alternate_text: "",
                  nemsis_element_ref: "",
                  nemsis_value_set: "",
                  active: true,
                  sort_order: 0,
                })
              }}
              className="ml-auto px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-medium"
            >
              + Add entry
            </button>
          </div>

          {/* Form */}
          {showForm && (
            <section className="mb-8 rounded-2xl border border-white/10 bg-white/5 p-6">
              <h3 className="text-lg font-semibold text-white mb-4">
                {editingId ? "Edit entry" : "New terminology entry"}
              </h3>
              <form onSubmit={handleSubmit} className="space-y-5 max-w-2xl">
                {!editingId && (
                  <>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm text-zinc-400 mb-1.5">Code set</label>
                        <select
                          value={form.code_set}
                          onChange={(e) => setForm((f) => ({ ...f, code_set: e.target.value }))}
                          className="w-full bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5"
                        >
                          {CODE_SETS.map(({ value, label }) => (
                            <option key={value} value={value}>{label}</option>
                          ))}
                        </select>
                      </div>
                      {form.code_set === "icd10" && (
                        <div>
                          <label className="block text-sm text-zinc-400 mb-1.5">Use case</label>
                          <select
                            value={form.use_case}
                            onChange={(e) => setForm((f) => ({ ...f, use_case: e.target.value }))}
                            className="w-full bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5"
                          >
                            {USE_CASES_ICD10.map(({ value, label }) => (
                              <option key={value} value={value}>{label}</option>
                            ))}
                          </select>
                        </div>
                      )}
                      {(form.code_set === "snomed" || form.code_set === "rxnorm") && (
                        <div>
                          <label className="block text-sm text-zinc-400 mb-1.5">Use case</label>
                          <input
                            type="text"
                            value={form.use_case}
                            onChange={(e) => setForm((f) => ({ ...f, use_case: e.target.value }))}
                            placeholder={form.code_set === "snomed" ? "e.g. intervention" : "e.g. medication"}
                            className="w-full bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5"
                          />
                        </div>
                      )}
                    </div>
                    <div>
                      <label className="block text-sm text-zinc-400 mb-1.5">Code *</label>
                      <input
                        required
                        value={form.code}
                        onChange={(e) => setForm((f) => ({ ...f, code: e.target.value }))}
                        className="w-full bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5"
                        placeholder="e.g. R50.9 or 1234567890"
                      />
                    </div>
                  </>
                )}
                <div>
                  <label className="block text-sm text-zinc-400 mb-1.5">Description *</label>
                  <input
                    required
                    value={form.description}
                    onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                    className="w-full bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5"
                    placeholder="Display text"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-zinc-400 mb-1.5">Alternate text</label>
                    <input
                      value={form.alternate_text}
                      onChange={(e) => setForm((f) => ({ ...f, alternate_text: e.target.value }))}
                      className="w-full bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-zinc-400 mb-1.5">NEMSIS element ref</label>
                    <input
                      value={form.nemsis_element_ref}
                      onChange={(e) => setForm((f) => ({ ...f, nemsis_element_ref: e.target.value }))}
                      placeholder="e.g. eChiefComplaint.02"
                      className="w-full bg-zinc-800/80 text-white border border-zinc-600 rounded-xl px-4 py-2.5"
                    />
                  </div>
                </div>
                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 text-zinc-300 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={form.active}
                      onChange={(e) => setForm((f) => ({ ...f, active: e.target.checked }))}
                      className="rounded border-zinc-600"
                    />
                    Active
                  </label>
                  <label className="flex items-center gap-2 text-zinc-300">
                    <span className="text-sm">Sort order</span>
                    <input
                      type="number"
                      value={form.sort_order}
                      onChange={(e) => setForm((f) => ({ ...f, sort_order: Number(e.target.value) || 0 }))}
                      className="w-24 bg-zinc-800/80 text-white border border-zinc-600 rounded-lg px-3 py-1.5"
                    />
                  </label>
                </div>
                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    className="px-5 py-2.5 rounded-xl bg-orange-600 hover:bg-orange-500 text-white font-medium"
                  >
                    {editingId ? "Update" : "Create"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-5 py-2.5 rounded-xl bg-zinc-700 hover:bg-zinc-600 text-white"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </section>
          )}

          {/* Entries */}
          <section className="rounded-2xl border border-white/10 bg-white/5 overflow-hidden">
            <div className="px-6 py-4 border-b border-white/10">
              <h3 className="text-lg font-semibold text-white">Entries</h3>
              <p className="text-zinc-500 text-sm mt-0.5">
                {codeSetFilter ? `Filtered by ${codeSetFilter}` : "All code sets"} · {entries.length} total
              </p>
            </div>
            {loading ? (
              <div className="p-12 text-center text-zinc-500">Loading…</div>
            ) : entries.length === 0 ? (
              <div className="p-12 text-center">
                <div className="text-5xl mb-4 opacity-60">📋</div>
                <p className="text-zinc-500 mb-2">No terminology entries yet.</p>
                <p className="text-zinc-600 text-sm">Use AI suggest above or Add entry to create ICD-10, SNOMED, or RXNorm codes.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-zinc-400 border-b border-zinc-800 bg-zinc-900/30">
                      <th className="pb-3 pt-3 px-6">Code set</th>
                      <th className="pb-3 pt-3 px-6">Use case</th>
                      <th className="pb-3 pt-3 px-6">Code</th>
                      <th className="pb-3 pt-3 px-6">Description</th>
                      <th className="pb-3 pt-3 px-6">NEMSIS ref</th>
                      <th className="pb-3 pt-3 px-6">Active</th>
                      <th className="pb-3 pt-3 px-6">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry) => (
                      <tr key={entry.id} className="border-b border-zinc-800/80 hover:bg-white/5 transition-colors">
                        <td className="py-3 px-6 text-zinc-300">{entry.code_set}</td>
                        <td className="py-3 px-6 text-zinc-300">{entry.use_case}</td>
                        <td className="py-3 px-6 font-mono text-orange-400">{entry.code}</td>
                        <td className="py-3 px-6 text-zinc-300">{entry.description}</td>
                        <td className="py-3 px-6 text-zinc-500">{entry.nemsis_element_ref ?? "—"}</td>
                        <td className="py-3 px-6">
                          <span className={entry.active ? "text-emerald-400" : "text-zinc-500"}>
                            {entry.active ? "Yes" : "No"}
                          </span>
                        </td>
                        <td className="py-3 px-6">
                          <button
                            type="button"
                            onClick={() => handleEdit(entry)}
                            className="text-orange-400 hover:text-orange-300 mr-3 font-medium"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDelete(entry.id)}
                            className="text-red-400 hover:text-red-300 font-medium"
                          >
                            Remove
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  )
}
