"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"

type EmailStats = {
  unread_messages: number
  messages_needing_response: number
  failed_deliveries_24h: number
  recent_activity_7d: number
  avg_response_minutes: number
  sender_status: string
}

type EmailMessage = {
  id: number
  direction: string
  sender: string
  recipients: string[]
  subject: string
  body_preview: string
  status: string
  created_at: string
  is_read: boolean
  needs_response: boolean
  message_id: string
  urgent?: boolean
}

type EmailDraft = {
  to: string
  subject: string
  body_text: string
  body_html?: string
  cc?: string[]
  bcc?: string[]
  reply_to?: string
  urgent?: boolean
}

export function EmailDashboardWidget() {
  const [emailStats, setEmailStats] = useState<EmailStats | null>(null)
  const [recentEmails, setRecentEmails] = useState<EmailMessage[]>([])
  const [needResponse, setNeedResponse] = useState<EmailMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [isComposing, setIsComposing] = useState(false)
  const [draft, setDraft] = useState<EmailDraft>({
    to: "",
    subject: "",
    body_text: ""
  })
  const [aiSuggestions, setAiSuggestions] = useState<string[]>([])

  useEffect(() => {
    let mounted = true
    
    const fetchData = () => {
      // Fetch email stats
      apiFetch<{stats: EmailStats}>("/api/founder/email/stats")
        .then(data => {
          if (mounted) setEmailStats(data.stats)
        })
        .catch(() => mounted && setEmailStats(null))
      
      // Fetch recent emails
      apiFetch<{emails: EmailMessage[]}>("/api/founder/email/recent?limit=15")
        .then(data => {
          if (mounted) setRecentEmails(data.emails)
        })
        .catch(() => mounted && setRecentEmails([]))
      
      // Fetch emails needing response - CRITICAL
      apiFetch<{emails: EmailMessage[]}>("/api/founder/email/needs-response?limit=10")
        .then(data => {
          if (mounted) setNeedResponse(data.emails)
        })
        .catch(() => mounted && setNeedResponse([]))
    }
    
    fetchData()
    const interval = setInterval(fetchData, 30000)  // Every 30s for founder priority
    
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const handleSendEmail = async () => {
    try {
      const response = await apiFetch("/api/founder/email/send", {
        method: "POST",
        body: JSON.stringify(draft),
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (response.success) {
        // Reset form
        setDraft({ to: "", subject: "", body_text: "" })
        setIsComposing(false)
        
        // Refresh data
        await fetchData()
        alert('Email sent successfully!')
      } else {
        alert('Failed to send email')
      }
    } catch (error) {
      console.error('Error sending email:', error)
      alert('Error sending email')
    }
  }

  const handleAIAssist = async () => {
    if (!draft.context) {
      alert('Please provide context for email generation')
      return
    }
    
    try {
      const aiDraft = await apiFetch('/api/founder/email/draft', {
        method: 'POST',
        body: JSON.stringify({
          recipient_email: draft.to,
          subject_context: draft.subject,
          context: draft.context,
          tone: "professional",
          length: "medium"
        }),
        headers: { 'Content-Type': 'application/json' }
      })
      
      if (aiDraft.success) {
        setDraft({
          ...draft,
          subject: aiDraft.subject,
          body_text: aiDraft.body_text
        })
      }
    } catch (error) {
      console.error('AI assist failed:', error)
    }
  }

  const handleSuggestImprovements = async () => {
    if (!draft.subject || !draft.context) {
      return
    }
    
    try {
      const suggestions = await apiFetch('/api/founder/email/suggest-improvements', {
        method: 'POST',
        body: JSON.stringify({
          recipient_email: draft.to,
          subject_line: draft.subject,
          context: draft.context
        }),
        headers: { 'Content-Type': 'application/json' }
      })
      
      setAiSuggestions(suggestions.suggestions)
    } catch (error) {
      console.error('Suggestions failed:', error)
    }
  }

  if (loading || !emailStats) {
    return (
      <section className="panel">
        <header>
          <h3>Email Dashboard</h3>
        </header>
        <div className="panel-card">
          <p className="muted-text">Loading email dashboard...</p>
        </div>
      </section>
    )
  }

  return (
    <section className="panel">
      <header>
        <h3>Email Dashboard</h3>
        <p className="muted-text">Founder email communications 6 Postmark integration</p>
      </header>

      {emailStats.sender_status === "needs_setup" && (
        <div className="platform-card muted">
          <strong>⚠️ Email Not Configured</strong>
          <p className="muted-text">Email service needs setup in organization settings</p>
        </div>
      )}

      {emailStats.sender_status === "active" && (
        <>
          {/* EMAIL STATS - PRIORITY SHOW */}
          <div className="platform-card-grid">
            <article className={`platform-card ${emailStats.unread_messages > 0 ? "warning" : ""}`}>
              <p className="muted-text">Unread Messages</p>
              <strong>{emailStats.unread_messages}</strong>
              {emailStats.unread_messages > 0 && (
                <span className="alert-badge"></span>
              )}
            </article>
            
            <article className={`platform-card ${emailStats.messages_needing_response > 0 ? "warning" : ""}`}>
              <p className="muted-text">Need Response</p>
              <strong>{emailStats.messages_needing_response}</strong>
              {emailStats.messages_needing_response > 0 && (
                <span className="alert-badge"></span>
              )}
            </article>
            
            <article className={`platform-card ${emailStats.failed_deliveries_24h > 0 ? "error" : ""}`}>
              <p className="muted-text">Failed (24h)</p>
              <strong>{emailStats.failed_deliveries_24h}</strong>
            </article>
            
            <article className="platform-card">
              <p className="muted-text">Recent (7d)</p>
              <strong>{emailStats.recent_activity_7d}</strong>
            </article>
          </div>

          {/* URGENT EMAILS NEEDING RESPONSE - CRITICAL */}
          {needResponse.length > 0 && (
            <div className="platform-card warning">
              <strong>🚨 {needResponse.length} Emails Need Response</strong>
              <ul className="needs-response-list">
                {needResponse.map((email) => (
                  <li key={email.id} className={`needs-response-item ${email.urgency === 'high' ? 'urgent' : ''}`}>
                    <span className="from">{email.from_address}</span>
                    <span className="subject">{email.subject}</span>
                    <span className="time">{new Date(email.created_at).toLocaleTimeString()}</span>
                    {email.urgency === 'high' && (
                      <span className="urgency">⚠️ URGENT</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        
          {/* RECENT EMAILS FEED */}
          <div className="recent-emails">
            <h4>Recent Emails</h4>
            <ul className="email-list">
              {recentEmails.map((email) => (
                <li key={email.id} className={`email-item ${email.direction} ${email.needs_response ? 'needs-response' : ''}`}>
                  <div className="email-meta">
                    <span className="direction">{email.direction === 'inbound' ? '📥' : '📤'}</span>
                    <span className="sender">{email.sender || email.recipients[0]}</span>
                    <span className="time">{new Date(email.created_at).toLocaleTimeString()}</span>
                    {email.needs_response && (
                      <span className="needs-response-badge">RESPOND</span>
                    )}
                  </div>
                  <p className="subject">{email.subject}</p>
                  <p className="preview">{email.body_preview}</p>
                </li>
              ))}
            </ul>
          </div>

          {/* COMPOSE EMAIL - FOUNDER DIRECT CONTROL */}
          <div className="email-compose">
            <h4>Compose New Email</h4>
            {!isComposing ? (
              <button className="compose-button primary" onClick={() => setIsComposing(true)}>
                ✉ Compose Email
              </button>
            ) : (
              <div className="compose-form">
                <div className="form-group">
                  <label>To:</label>
                  <input
                    type="email"
                    value={draft.to}
                    onChange={(e) => setDraft({...draft, to: e.target.value})}
                    placeholder="recipient@example.com"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Subject:</label>
                  <input
                    type="text"
                    value={draft.subject}
                    onChange={(e) => setDraft({...draft, subject: e.target.value})}
                    placeholder="Email subject"
                    required
                  />
                </div>
                
                <div className="form-group">
                  <label>Message:</label>
                  <textarea
                    value={draft.body_text}
                    onChange={(e) => setDraft({...draft, body_text: e.target.value})}
                    placeholder="Type your message here..."
                    rows={5}
                    required
                  />
                </div>
                
                <div className="form-actions">
                  <button className="send-button" onClick={handleSendEmail}>
                    📤 Send Email
                  </button>
                  <button className="ai-button" onClick={handleAIAssist}>
                    🤖 AI Help
                  </button>
                  <button className="cancel-button" onClick={() => setIsComposing(false)}>
                    Cancel
                  </button>
                </div>
                
                {aiSuggestions.length > 0 && (
                  <div className="ai-suggestions">
                    <h5>AI Suggestions</h5>
                    <ul>
                      {aiSuggestions.map((suggestion, i) => (
                        <li key={i}>{suggestion}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}

      <style jsx>{`
        .needs-response-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .needs-response-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.75rem;
          border-left: 3px solid #ff9800;
          background: rgba(255, 152, 0, 0.05);
          margin-bottom: 0.5rem;
          border-radius: 4px;
        }
        .needs-response-item.urgent {
          border-left: 3px solid #f44336;
          background: rgba(244, 67, 54, 0.05);
        }
        .needs-response-item .from {
          font-weight: 600;
          font-size: 0.9rem;
        }
        .needs-response-item .subject {
          font-size: 0.85rem;
          color: #666;
          flex: 1;
          text-align: center;
        }
        .needs-response-item .time {
          font-size: 0.8rem;
          color: #666;
        }
        .needs-response-item .needs-response-badge {
          background: #ff9800;
          color: white;
          padding: 0.25rem 0.5rem;
          border-radius: 3px;
          font-size: 0.75rem;
          font-weight: 600;
        }
        .recent-emails .email-list {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        .email-list .email-item {
          padding: 0.75rem;
          border-bottom: 1px solid #e0e0e0;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 0.75rem;
        }
        .email-list .email-item:last-child {
          border-bottom: none;
        }
        .email-list .email-item.inbound {
          border-left: 3px solid #4caf50;
          background: rgba(76, 175, 80, 0.05);
        }
        .email-list .email-item.outbound {
          border-left: 3px solid #2196f3;
          background: rgba(33, 150, 243, 0.05);
        }
        .email-list .email-item.needs-response {
          border-left: 3px solid #ff9800;
          background: rgba(255, 152, 0, 0.1);
        }
        .email-list .email-item .email-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.25rem;
          width: 100%;
        }
        .email-list .email-item .direction {
          font-size: 0.875rem;
          margin-right: 0.5rem;
        }
        .email-list .email-item .sender {
          font-weight: 600;
          font-size: 0.9rem;
        }
        .email-list .email-item .subject {
          font-size: 0.85rem;
          color: #333;
          margin: 0.25rem 0;
        }
        .email-list .email-item .preview {
          font-size: 0.8rem;
          color: #666;
          margin: 0;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .email-list .email-item .time {
          font-size: 0.75rem;
          color: #999;
        }
        .email-list .email-item .needs-response-badge {
          background: #ff9800;
          color: white;
          padding: 0.2rem 0.4rem;
          border-radius: 3px;
          font-size: 0.65rem;
          font-weight: 600;
        }
        .email-compose {
          margin-top: 1rem;
          padding: 1rem;
          background: #f8f9fa;
          border-radius: 6px;
        }
        .compose-form {
          width: 100%;
        }
        .form-group {
          margin-bottom: 1rem;
        }
        .form-group label {
          display: block;
          font-weight: 500;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
        }
        .form-group input,
        .form-group textarea {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 0.9rem;
          font-family: inherit;
        }
        .form-group input:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #2196f3;
          box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
        }
        .form-group textarea {
          resize: vertical;
          min-height: 120px;
        }
        .form-actions {
          display: flex;
          gap: 0.75rem;
          margin-top: 1rem;
        }
        .send-button {
          background: #4caf50;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
          transition: background 0.2s;
        }
        .send-button:hover {
          background: #45a049;
        }
        .ai-button {
          background: #ff9800;
          color: white;
          border: none;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
          transition: background 0.2s;
        }
        .ai-button:hover {
          background: #f57c00;
        }
        .cancel-button {
          background: #f5f5f5;
          color: #666;
          border: 1px solid #ddd;
          padding: 0.75rem 1.5rem;
          border-radius: 4px;
          cursor: pointer;
          font-weight: 500;
          transition: background 0.2s;
        }
        .cancel-button:hover {
          background: #e0e0e0;
        }
        .ai-suggestions {
          margin-top: 1rem;
          padding: 1rem;
          background: #fff;
          border-left: 3px solid #ff9800;
          border-radius: 4px;
        }
        .ai-suggestions h5 {
          margin: 0 0 0.5rem 0;
          color: #f57c00;
          font-size: 0.9rem;
        }
        .ai-suggestions ul {
          margin: 0;
          padding-left: 1.25rem;
        }
        .ai-suggestions li {
          margin: 0.25rem 0;
          font-size: 0.85rem;
        }
        .alert-badge {
          width: 8px;
          height: 8px;
          background: #ff9800;
          border-radius: 50%;
          margin-left: 0.5rem;
        }
      `}</style>
    </section>
  )
}
