"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"

interface BillingStats {
  unpaid_claims_value: number
  overdue_claims_value: number
  avg_days_to_payment: number
  billing_accuracy_score: number
  claims_out_for_review: number
  payer_responses_pending: number
  draft_invoices_count: number
  draft_invoices_value: number
  potential_billing_issues: number
  ai_suggestions_available: number
}

interface RecentBillingActivity {
  id: string
  date: string
  type: string
  payer: string
  amount: number
  status: string
  ai_flagged: boolean
}

interface AIInsight {
  category: "billing_issue" | "optimization" | "urgent_action"
  title: string
  description: string
  impact: "high" | "medium" | "low"
  related_claims?: string[]
  suggested_action: string
  ai_confidence: number
}

export default function AIBillingWidget() {
  const [stats, setStats] = useState<BillingStats | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentBillingActivity[]>([])
  const [aiInsights, setAiInsights] = useState<AIInsight[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>("")
  const [showAIChat, setShowAIChat] = useState(false)
  const [chatQuestion, setChatQuestion] = useState("")
  const [chatResponse, setChatResponse] = useState("")
  const [loadingChat, setLoadingChat] = useState(false)

  useEffect(() => {
    let mounted = true
    
    const fetchBillingData = async () => {
      try {
        const [statsData, activityData, insightsData] = await Promise.all([
          apiFetch<BillingStats>("/api/founder/billing/stats"),
          apiFetch<RecentBillingActivity[]>("/api/founder/billing/recent-activity"),
          apiFetch<AIInsight[]>("/api/founder/billing/ai-insights")
        ])
        
        if (mounted) {
          setStats(statsData)
          setRecentActivity(activityData)
          setAiInsights(insightsData)
          setLoading(false)
        }
      } catch (err) {
        if (mounted) {
          setError("Failed to load billing data")
          setLoading(false)
        }
      }
    }

    fetchBillingData()
    
    // Auto-refresh every 60 seconds for billing
    const interval = setInterval(fetchBillingData, 60000)
    
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const handleAIChat = async () => {
    if (!chatQuestion.trim()) return
    
    setLoadingChat(true)
    try {
      const response = await apiFetch<{ response: string }>("/api/founder/billing/ai-chat", {
        method: "POST",
        body: JSON.stringify({ question: chatQuestion })
      })
      setChatResponse(response.response)
    } catch (err) {
      setChatResponse("Sorry, I encountered an error processing your question. Please try again.")
    } finally {
      setLoadingChat(false)
    }
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  if (loading) {
    return (
      <section className="panel">
        <header>
          <h3>AI Billing Assistant</h3>
        </header>
        <div className="data-grid">
          <p className="muted-text">Loading billing data...</p>
        </div>
      </section>
    )
  }

  if (error) {
    return (
      <section className="panel">
        <header>
          <h3>AI Billing Assistant</h3>
        </header>
        <div className="data-grid">
          <p className="warning-text">{error}</p>
        </div>
      </section>
    )
  }

  return (
    <div className="panel-stack">
      {/* Main Stats */}
      <section className="panel">
        <header>
          <h3>AI Billing Assistant</h3>
          <span className="status-pill status-healthy">{stats?.ai_suggestions_available || 0} AI Suggestions</span>
        </header>
        <div className="data-grid">
          <article className="panel-card">
            <p className="muted-text">Unpaid Claims</p>
            <strong className={stats?.unpaid_claims_value > 50000 ? "warning-text" : ""}>
              {formatCurrency(stats?.unpaid_claims_value || 0)}
            </strong>
          </article>
          
          <article className="panel-card">
            <p className="muted-text">Overdue Claims</p>
            <strong className={stats?.overdue_claims_value > 10000 ? "warning-text" : ""}>
              {formatCurrency(stats?.overdue_claims_value || 0)}
            </strong>
          </article>
          
          <article className="panel-card">
            <p className="muted-text">Avg Days to Payment</p>
            <strong>{stats?.avg_days_to_payment || 0}</strong>
          </article>
          
          <article className="panel-card">
            <p className="muted-text">Billing Accuracy</p>
            <strong className={stats?.billing_accuracy_score > 85 ? "success-text" : "warning-text"}>
              {stats?.billing_accuracy_score || 0}%
            </strong>
          </article>
          
          <article className="panel-card">
            <p className="muted-text">Claims Out for Review</p>
            <strong>{stats?.claims_out_for_review || 0}</strong>
          </article>
          
          <article className="panel-card">
            <p className="muted-text">Payer Responses Pending</p>
            <strong>{stats?.payer_responses_pending || 0}</strong>
          </article>
        </div>
        
        <div className="panel-stack" style={{ marginTop: "1rem" }}>
          <button 
            className="cta-button cta-primary"
            onClick={() => setShowAIChat(!showAIChat)}
          >
            Ask AI Billing Assistant
          </button>
          <Link 
            href="/founder/billing/dashboard"
            className="cta-button cta-secondary"
          >
            Full Billing Dashboard
          </Link>
        </div>
      </section>

      {/* AI Chat Panel */}
      {showAIChat && (
        <section className="panel">
          <header>
            <h3>AI Billing Chat</h3>
          </header>
          <div className="chat-container" style={{ marginBottom: "1rem" }}>
            <textarea
              className="chat-input"
              placeholder="Ask about billing, claims, denials, insurance questions..."
              value={chatQuestion}
              onChange={(e) => setChatQuestion(e.target.value)}
              rows={3}
              style={{ width: "100%", marginBottom: "0.5rem" }}
            />
            <button 
              className="cta-button cta-primary"
              onClick={handleAIChat}
              disabled={loadingChat || !chatQuestion.trim()}
            >
              {loadingChat ? "Thinking..." : "Ask AI"}
            </button>
            
            {chatResponse && (
              <div className="chat-response" style={{ marginTop: "1rem", padding: "1rem", background: "var(--bg-secondary)" }}>
                <strong>AI Assistant:</strong>
                <p>{chatResponse}</p>
              </div>
            )}
          </div>
        </section>
      )}

      {/* AI Insights */}
      {aiInsights.length > 0 && (
        <section className="panel">
          <header>
            <h3>AI Billing Insights</h3>
          </header>
          <div className="data-grid">
            {aiInsights.map((insight, index) => (
              <article 
                key={index} 
                className={`panel-card ${insight.category === "urgent_action" ? "warning" : insight.category === "billing_issue" ? "error" : ""}`}
              >
                <div>
                  <strong>{insight.title}</strong>
                  <p className="muted-text">{insight.description}</p>
                  <p className="muted-text">
                    Impact: <strong className={insight.impact === "high" ? "warning-text" : ""}>
                      {insight.impact}
                    </strong>
                  </p>
                  <p className="muted-text">
                    AI Confidence: {(insight.ai_confidence * 100).toFixed(0)}%
                  </p>
                </div>
                {insight.suggested_action && (
                  <button className="cta-button cta-secondary cta-sm">
                    {insight.suggested_action}
                  </button>
                )}
              </article>
            ))}
          </div>
        </section>
      )}

      {/* Recent Activity */}
      <section className="panel">
        <header>
          <h3>Recent Billing Activity</h3>
        </header>
        <div className="data-grid">
          {recentActivity.slice(0, 5).map((activity) => (
            <article key={activity.id} className={`panel-card ${activity.ai_flagged ? "warning" : ""}`}>
              <div>
                <strong>{activity.type}</strong>
                <p className="muted-text">{activity.payer}</p>
                {activity.ai_flagged && (
                  <span className="status-pill status-warning">AI Flagged</span>
                )}
              </div>
              <div>
                <strong>{formatCurrency(activity.amount)}</strong>
                <p className="muted-text">{activity.status}</p>
                <p className="muted-text">{activity.date}</p>
              </div>
            </article>
          ))}
          {recentActivity.length === 0 && (
            <p className="muted-text">No recent billing activity</p>
          )}
        </div>
      </section>
    </div>
  )
}