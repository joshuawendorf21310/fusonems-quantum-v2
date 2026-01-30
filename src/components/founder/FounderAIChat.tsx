"use client"

import React, { useCallback, useRef, useState } from "react"
import { apiClient } from "@/lib/api"

type MessageRole = "user" | "assistant" | "system"

interface ChatMessage {
  role: MessageRole
  content: string
  actionsTaken?: { action: string; result: string; detail?: string }[]
}

const QUICK_ACTIONS = [
  { label: "Fix issues", prompt: "What’s broken and how do I fix it? Run any safe fixes." },
  { label: "Suggest enhancements", prompt: "Suggest concrete enhancements for the platform based on current health and queue." },
  { label: "Run health check", prompt: "Summarize system health and any critical or warning issues." },
  { label: "Self-heal (safe fixes)", prompt: "Run self-heal: retry failed jobs and check NEMSIS. Then summarize what you did." },
]

export default function FounderAIChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "I’m your FusionEMS Quantum assistant. I can **fix** issues, **add** or **enhance** features, **suggest** improvements, and run **self-healing** (retry failed jobs, NEMSIS check). Use the quick actions below or type your own request. Enable “Allow self-healing” to let me run safe automated fixes when you ask.",
    },
  ])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [allowSelfHeal, setAllowSelfHeal] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [])

  const handleSend = useCallback(
    async (text?: string) => {
      const toSend = (text ?? input).trim()
      if (!toSend) return

      setInput("")
      setMessages((msgs) => [...msgs, { role: "user", content: toSend }])
      setLoading(true)

      try {
        const history = messages
          .filter((m) => m.role === "user" || m.role === "assistant")
          .map((m) => ({ role: m.role, content: m.content }))

        const { data } = await apiClient.post<{ reply: string; actions_taken?: { action: string; result: string; detail?: string }[] }>(
          "/api/founder/ai-assistant/chat",
          {
            message: toSend,
            allow_self_heal: allowSelfHeal,
            history,
          }
        )

        setMessages((msgs) => [
          ...msgs,
          {
            role: "assistant",
            content: data.reply || "No response from assistant.",
            actionsTaken: data.actions_taken?.length ? data.actions_taken : undefined,
          },
        ])
      } catch (err) {
        const message = err && typeof err === "object" && "message" in err ? String((err as { message: unknown }).message) : "Request failed."
        setMessages((msgs) => [
          ...msgs,
          { role: "assistant", content: `Error: ${message}. Check that the backend is running and you’re signed in.` },
        ])
      } finally {
        setLoading(false)
        setTimeout(scrollToBottom, 100)
      }
    },
    [input, allowSelfHeal, messages, scrollToBottom]
  )

  const handleQuickAction = useCallback(
    (prompt: string) => {
      setInput(prompt)
      if (prompt.toLowerCase().includes("self-heal")) {
        setAllowSelfHeal(true)
      }
      setTimeout(() => handleSend(prompt), 0)
    },
    [handleSend]
  )

  return (
    <div
      className="flex flex-col rounded-2xl border border-white/10 bg-zinc-900/80 shadow-xl"
      style={{ minHeight: 420, maxHeight: "calc(100vh - 220px)" }}
    >
      <div className="flex items-center justify-between gap-4 border-b border-white/10 px-4 py-3">
        <h2 className="text-lg font-semibold text-white">AI Assistant</h2>
        <label className="flex items-center gap-2 text-sm text-zinc-300">
          <input
            type="checkbox"
            checked={allowSelfHeal}
            onChange={(e) => setAllowSelfHeal(e.target.checked)}
            className="h-4 w-4 rounded border-zinc-500 bg-zinc-800 text-amber-500 focus:ring-amber-500"
          />
          Allow self-healing
        </label>
      </div>

      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4"
        style={{ minHeight: 240 }}
      >
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`mb-4 flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
                msg.role === "user"
                  ? "bg-blue-600 text-white"
                  : msg.role === "assistant"
                    ? "bg-zinc-700/90 text-zinc-100"
                    : "bg-zinc-800 text-zinc-400"
              }`}
            >
              {msg.role === "assistant" && msg.actionsTaken && msg.actionsTaken.length > 0 && (
                <div className="mb-2 rounded-lg border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-xs text-amber-200">
                  <span className="font-medium">Actions taken:</span>
                  <ul className="mt-1 list-inside list-disc space-y-0.5">
                    {msg.actionsTaken.map((a, j) => (
                      <li key={j}>
                        {a.action}: {a.result}
                        {a.detail ? ` — ${a.detail}` : ""}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div
                className="prose prose-invert prose-sm max-w-none text-sm leading-relaxed [&_code]:rounded [&_code]:bg-zinc-600 [&_code]:px-1 [&_code]:py-0.5 [&_code]:text-amber-200"
                dangerouslySetInnerHTML={{
                  __html: simpleMarkdown(msg.content),
                }}
              />
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-2xl bg-zinc-700/90 px-4 py-2.5 text-sm text-zinc-300">
              Thinking…
            </div>
          </div>
        )}
      </div>

      <div className="flex flex-wrap gap-2 border-t border-white/10 p-3">
        {QUICK_ACTIONS.map((q) => (
          <button
            key={q.label}
            type="button"
            onClick={() => handleQuickAction(q.prompt)}
            disabled={loading}
            className="rounded-full border border-white/20 bg-white/5 px-3 py-1.5 text-xs font-medium text-zinc-300 transition hover:bg-white/10 hover:text-white disabled:opacity-50"
          >
            {q.label}
          </button>
        ))}
      </div>

      <div className="flex gap-2 border-t border-white/10 p-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Type your request, question, or command…"
          disabled={loading}
          className="flex-1 rounded-xl border border-white/10 bg-zinc-800 px-4 py-2.5 text-sm text-white placeholder-zinc-500 focus:border-amber-500 focus:outline-none focus:ring-1 focus:ring-amber-500 disabled:opacity-60"
        />
        <button
          type="button"
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-semibold text-zinc-900 shadow transition hover:bg-amber-400 disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  )
}

function simpleMarkdown(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`(.+?)`/g, "<code class=\"rounded bg-zinc-600 px-1 py-0.5 text-amber-200\">$1</code>")
    .replace(/\n/g, "<br />")
}
