"use client";
import React, { useRef, useState } from "react"

interface Transaction {
  id: string
  date: string
  description: string
  amount: number
  type: "credit" | "debit"
  category?: string
  source: "imported" | "manual"
}

interface BankCardImportWidgetProps {
  onTransactionsImported?: (txns: Transaction[]) => void
}

const EXAMPLE_CSV = `date,description,amount,type\n2026-01-01,AMEX PAYMENT,-1000,debit\n2026-01-02,NOVO DEPOSIT,5000,credit`;

export default function BankCardImportWidget({ onTransactionsImported }: BankCardImportWidgetProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [importError, setImportError] = useState<string>("")
  const [showManual, setShowManual] = useState(false)
  const [categorizing, setCategorizing] = useState(false)
  const [showReview, setShowReview] = useState(false)
  const [reviewTxns, setReviewTxns] = useState<Transaction[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  function parseCSV(csv: string): Transaction[] {
    const lines = csv.trim().split("\n")
    const [header, ...rows] = lines
    return rows.map((row, idx) => {
      const [date, description, amount, type] = row.split(",")
      return {
        id: `imported-${idx}-${date}`,
        date,
        description,
        amount: parseFloat(amount),
        type: type as "credit" | "debit",
        source: "imported"
      }
    })
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (evt) => {
      try {
        const text = evt.target?.result as string
        const txns = parseCSV(text)
        setTransactions((prev) => [...prev, ...txns])
        setImportError("")
        onTransactionsImported?.(txns)
      } catch {
        setImportError("Failed to parse file. Please use CSV format.")
      }
    }
    reader.readAsText(file)
  }

  function handleManualAdd(txn: Omit<Transaction, "id" | "source">) {
    setTransactions((prev) => [
      ...prev,
      { ...txn, id: `manual-${Date.now()}`, source: "manual" }
    ])
    setShowManual(false)
  }

  async function handleCategorize() {
    setCategorizing(true)
    try {
      const res = await fetch("/api/ai/categorize-transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ transactions })
      })
      if (!res.ok) throw new Error("Failed to categorize")
      const data = await res.json()
      setReviewTxns(data.categorized)
      setShowReview(true)
    } catch {
      setImportError("AI categorization failed.")
    } finally {
      setCategorizing(false)
    }
  }

  function handleCategoryChange(idx: number, newCat: string) {
    setReviewTxns((prev) => prev.map((t, i) => i === idx ? { ...t, category: newCat } : t))
  }

  function handleReviewSave() {
    setTransactions(reviewTxns)
    setShowReview(false)
  }

  return (
    <section className="panel mb-8">
      <header>
        <h3>Bank & Credit Card Import</h3>
        <p className="muted-text">Import transactions from Novo, Amex, or upload CSV/OFX/QFX. Add missing transactions manually.</p>
      </header>
      <div className="flex gap-4 items-center mb-4">
        <input
          type="file"
          accept=".csv,.ofx,.qfx"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
        />
        <button className="btn-primary" onClick={() => fileInputRef.current?.click()}>
          Import CSV/OFX/QFX
        </button>
        <button className="btn-secondary" onClick={() => setShowManual(true)}>
          Add Transaction Manually
        </button>
        <a
          href={`data:text/csv;charset=utf-8,${encodeURIComponent(EXAMPLE_CSV)}`}
          download="example.csv"
          className="text-blue-700 underline ml-2"
        >
          Example CSV
        </a>
        <button
          className="btn-accent ml-auto"
          disabled={!transactions.length || categorizing}
          onClick={handleCategorize}
        >
          {categorizing ? "Categorizing..." : "AI Categorize & Review"}
        </button>
      </div>
      {importError && <div className="text-red-600 mb-2">{importError}</div>}
      {showManual && (
        <ManualTransactionForm onAdd={handleManualAdd} onCancel={() => setShowManual(false)} />
      )}
      {showReview ? (
        <ReviewTable
          transactions={reviewTxns}
          onCategoryChange={handleCategoryChange}
          onSave={handleReviewSave}
          onCancel={() => setShowReview(false)}
        />
      ) : (
        <TransactionTable transactions={transactions} />
      )}
    </section>
  )
}

function ReviewTable({ transactions, onCategoryChange, onSave, onCancel }: {
  transactions: Transaction[],
  onCategoryChange: (idx: number, newCat: string) => void,
  onSave: () => void,
  onCancel: () => void
}) {
  const categories = [
    "Credit Card Payment",
    "Business Deposit",
    "Payroll",
    "Fuel",
    "Office Expense",
    "Insurance",
    "Tax Payment",
    "Deposit",
    "Payment",
    "Uncategorized"
  ]
  return (
    <div className="border rounded p-4 mb-4 bg-blue-50">
      <h4 className="font-bold mb-2">Review & Edit Categories</h4>
      <table className="w-full border mb-2">
        <thead>
          <tr className="bg-blue-100">
            <th className="p-2 border">Date</th>
            <th className="p-2 border">Description</th>
            <th className="p-2 border">Amount</th>
            <th className="p-2 border">Type</th>
            <th className="p-2 border">Category</th>
          </tr>
        </thead>
        <tbody>
          {transactions.map((txn, idx) => (
            <tr key={txn.id}>
              <td className="p-2 border">{txn.date}</td>
              <td className="p-2 border">{txn.description}</td>
              <td className="p-2 border">${txn.amount.toFixed(2)}</td>
              <td className="p-2 border">{txn.type}</td>
              <td className="p-2 border">
                <select value={txn.category || "Uncategorized"} onChange={e => onCategoryChange(idx, e.target.value)}>
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="flex gap-2 justify-end">
        <button className="btn-primary" onClick={onSave}>Save</button>
        <button className="btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </div>
  )
}

function ManualTransactionForm({ onAdd, onCancel }: { onAdd: (txn: Omit<Transaction, "id" | "source">) => void, onCancel: () => void }) {
  const [form, setForm] = useState({
    date: "",
    description: "",
    amount: "",
    type: "debit"
  })
  const [error, setError] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!form.date || !form.description || !form.amount) {
      setError("All fields required.")
      return
    }
    onAdd({
      date: form.date,
      description: form.description,
      amount: parseFloat(form.amount),
      type: form.type as "credit" | "debit",
    })
  }

  return (
    <form className="bg-blue-50 border border-blue-200 rounded p-4 mb-4" onSubmit={handleSubmit}>
      <div className="flex gap-2 mb-2">
        <input type="date" value={form.date} onChange={e => setForm(f => ({ ...f, date: e.target.value }))} className="border rounded px-2 py-1 flex-1" />
        <input type="text" placeholder="Description" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} className="border rounded px-2 py-1 flex-2" />
        <input type="number" placeholder="Amount" value={form.amount} onChange={e => setForm(f => ({ ...f, amount: e.target.value }))} className="border rounded px-2 py-1 flex-1" />
        <select value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))} className="border rounded px-2 py-1">
          <option value="debit">Debit</option>
          <option value="credit">Credit</option>
        </select>
      </div>
      {error && <div className="text-red-600 mb-2">{error}</div>}
      <div className="flex gap-2">
        <button type="submit" className="btn-primary">Add</button>
        <button type="button" className="btn-secondary" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

function TransactionTable({ transactions }: { transactions: Transaction[] }) {
  if (!transactions.length) return <div className="text-gray-500">No transactions imported yet.</div>
  return (
    <table className="w-full border mt-4">
      <thead>
        <tr className="bg-blue-100">
          <th className="p-2 border">Date</th>
          <th className="p-2 border">Description</th>
          <th className="p-2 border">Amount</th>
          <th className="p-2 border">Type</th>
          <th className="p-2 border">Source</th>
        </tr>
      </thead>
      <tbody>
        {transactions.map(txn => (
          <tr key={txn.id}>
            <td className="p-2 border">{txn.date}</td>
            <td className="p-2 border">{txn.description}</td>
            <td className="p-2 border">${txn.amount.toFixed(2)}</td>
            <td className="p-2 border">{txn.type}</td>
            <td className="p-2 border">{txn.source}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
