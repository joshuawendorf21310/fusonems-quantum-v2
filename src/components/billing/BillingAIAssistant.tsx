"use client"

import { useState } from "react"
import { apiFetch } from "@/lib/api"

const QUICK_TOPICS = [
  "What should I do next?",
  "Explain denial risk",
  "What is an EOB?",
  "Explain claim status",
  "What is NEMSIS?",
  "How do I submit a claim?",
]

type Tab = "explain" | "chat"

export default function BillingAIAssistant({ pageContext }: { pageContext?: string }) {
  const [tab, setTab] = useState<Tab>("explain")
  const [topic, setTopic] = useState("")
  const [context, setContext] = useState(pageContext ?? "")
  const [question, setQuestion] = useState("")
  const [explanation, setExplanation] = useState("")
  const [chatResponse, setChatResponse] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleExplain = async () => {
    const t = topic.trim() || "what to do next"
    setError("")
    setLoading(true)
    setExplanation("")
    try {
      const res = await apiFetch<{ explanation: string }>("/api/founder/billing/explain", {
        method: "POST",
        body: JSON.stringify({ topic: t, context: context.trim() || undefined }),
      })
      setExplanation(res.explanation)
    } catch (e) {
      setError("Could not get explanation. Try again or ask in the chat.")
    } finally {
      setLoading(false)
    }
  }

  const handleChat = async () => {
    if (!question.trim()) return
    setError("")
    setLoading(true)
    setChatResponse("")
    try {
      const res = await apiFetch<{ response: string }>("/api/founder/billing/ai-chat", {
        method: "POST",
        body: JSON.stringify({ question: question.trim() }),
      })
      setChatResponse(res.response)
    } catch (e) {
      setError("Could not get answer. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <section
      style={{
        padding: "1.25rem",
        borderRadius: 16,
        background: "rgba(17,17,17,0.9)",
        border: "1px solid rgba(255,255,255,0.1)",
        marginTop: "1.5rem",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "1rem" }}>
        <span style={{ fontSize: "1.25rem" }}>🤖</span>
        <h3 style={{ color: "#ff7c29", margin: 0, fontSize: "1.1rem" }}>
          Billing AI Assistant — New to billing? I explain everything.
        </h3>
      </div>

      <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1rem" }}>
        <button
          type="button"
          onClick={() => setTab("explain")}
          style={{
            padding: "0.4rem 0.8rem",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.2)",
            background: tab === "explain" ? "rgba(255,124,41,0.2)" : "transparent",
            color: "#f7f6f3",
            cursor: "pointer",
            fontSize: "0.9rem",
          }}
        >
          Explain a term
        </button>
        <button
          type="button"
          onClick={() => setTab("chat")}
          style={{
            padding: "0.4rem 0.8rem",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.2)",
            background: tab === "chat" ? "rgba(255,124,41,0.2)" : "transparent",
            color: "#f7f6f3",
            cursor: "pointer",
            fontSize: "0.9rem",
          }}
        >
          Ask the AI
        </button>
      </div>

      {tab === "explain" && (
        <>
          <p style={{ color: "#bbb", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
            Type a billing term or question (e.g. &quot;denial&quot;, &quot;what to do next&quot;). I&apos;ll explain in plain language.
          </p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
            {QUICK_TOPICS.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => { setTopic(t); setExplanation(""); }}
                style={{
                  padding: "0.35rem 0.65rem",
                  borderRadius: 6,
                  border: "1px solid rgba(255,255,255,0.15)",
                  background: "rgba(255,255,255,0.05)",
                  color: "#ddd",
                  cursor: "pointer",
                  fontSize: "0.8rem",
                }}
              >
                {t}
              </button>
            ))}
          </div>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleExplain()}
            placeholder="e.g. denial, EOB, claim status..."
            style={{
              width: "100%",
              maxWidth: 400,
              padding: "0.5rem 0.75rem",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.15)",
              background: "rgba(0,0,0,0.3)",
              color: "#f7f6f3",
              marginBottom: "0.5rem",
            }}
          />
          <input
            type="text"
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Where you are (optional): e.g. Billing dashboard, Denials page"
            style={{
              width: "100%",
              maxWidth: 400,
              padding: "0.4rem 0.75rem",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.1)",
              background: "rgba(0,0,0,0.2)",
              color: "#bbb",
              fontSize: "0.85rem",
              marginBottom: "0.75rem",
            }}
          />
          <button
            type="button"
            onClick={handleExplain}
            disabled={loading}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 8,
              border: "none",
              background: "#ff7c29",
              color: "#fff",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? "Getting explanation…" : "Explain"}
          </button>
          {explanation && (
            <div
              style={{
                marginTop: "1rem",
                padding: "1rem",
                borderRadius: 12,
                background: "rgba(0,0,0,0.3)",
                border: "1px solid rgba(255,255,255,0.06)",
                color: "#e0e0e0",
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
              }}
            >
              {explanation}
            </div>
          )}
        </>
      )}

      {tab === "chat" && (
        <>
          <p style={{ color: "#bbb", fontSize: "0.85rem", marginBottom: "0.75rem" }}>
            Ask anything about billing. I&apos;ll give plain-language answers and tell you what to do next.
          </p>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="e.g. I have 3 denied claims. What do I do first?"
            rows={3}
            style={{
              width: "100%",
              maxWidth: 500,
              padding: "0.6rem 0.75rem",
              borderRadius: 8,
              border: "1px solid rgba(255,255,255,0.15)",
              background: "rgba(0,0,0,0.3)",
              color: "#f7f6f3",
              marginBottom: "0.75rem",
              resize: "vertical",
            }}
          />
          <button
            type="button"
            onClick={handleChat}
            disabled={loading || !question.trim()}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 8,
              border: "none",
              background: "#ff7c29",
              color: "#fff",
              fontWeight: 600,
              cursor: loading || !question.trim() ? "not-allowed" : "pointer",
              opacity: loading || !question.trim() ? 0.7 : 1,
            }}
          >
            {loading ? "Thinking…" : "Ask the AI"}
          </button>
          {chatResponse && (
            <div
              style={{
                marginTop: "1rem",
                padding: "1rem",
                borderRadius: 12,
                background: "rgba(0,0,0,0.3)",
                border: "1px solid rgba(255,255,255,0.06)",
                color: "#e0e0e0",
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
              }}
            >
              {chatResponse}
            </div>
          )}
        </>
      )}

      {error && (
        <p style={{ color: "#f87171", fontSize: "0.85rem", marginTop: "0.75rem" }}>{error}</p>
      )}
    </section>
  )
}
