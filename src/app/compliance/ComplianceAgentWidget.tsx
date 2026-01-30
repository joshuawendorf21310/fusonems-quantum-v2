import { useState } from "react"

export default function ComplianceAgentWidget() {
  const [prompt, setPrompt] = useState("")
  const [answer, setAnswer] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setAnswer("")
    try {
      const res = await fetch("/api/ollama/agent", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      })
      const data = await res.json()
      setAnswer(data.answer)
    } catch {
      setAnswer("Error contacting compliance agent.")
    }
    setLoading(false)
  }

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-6 mt-8">
      <h3 className="text-lg font-semibold mb-2">Ask the Compliance AI Agent</h3>
      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          type="text"
          className="rounded-md px-3 py-2 text-black"
          placeholder="Ask a compliance or regulatory question..."
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          disabled={loading}
          required
        />
        <button
          type="submit"
          className="rounded-md bg-[#B86B1E] px-4 py-2 text-sm font-semibold text-black hover:bg-[#C87424] transition"
          disabled={loading}
        >
          {loading ? "Asking..." : "Ask Agent"}
        </button>
      </form>
      {answer && (
        <div className="mt-4 p-3 rounded bg-black/30 text-white/90 text-sm border border-white/10">
          {answer}
        </div>
      )}
    </div>
  )
}
