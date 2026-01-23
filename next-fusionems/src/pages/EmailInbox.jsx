import { useEffect, useMemo, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

const SYSTEM_LABELS = [
  { slug: 'billing', name: 'Billing', color: 'orange' },
  { slug: 'legal', name: 'Legal', color: 'red' },
  { slug: 'compliance', name: 'Compliance', color: 'blue' },
  { slug: 'ocr', name: 'OCR', color: 'teal' },
  { slug: 'ai-alert', name: 'AI Alert', color: 'purple' },
  { slug: 'medical-director', name: 'Medical Director', color: 'amber' },
  { slug: 'ops-admin', name: 'Ops / Admin', color: 'slate' },
]

const QUICK_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'billing', label: 'Billing' },
  { key: 'legal', label: 'Legal' },
  { key: 'compliance', label: 'Compliance' },
  { key: 'attachments', label: 'Has Attachments' },
]

const buildMatchReasons = (message, query) => {
  if (!query) {
    return []
  }
  const lowered = query.toLowerCase()
  const reasons = []
  if (message.subject?.toLowerCase().includes(lowered)) {
    reasons.push('Matched subject')
  }
  if (message.body_plain?.toLowerCase().includes(lowered)) {
    reasons.push('Matched body')
  }
  if (message.sender?.toLowerCase().includes(lowered)) {
    reasons.push('Matched sender')
  }
  return reasons.length ? reasons : ['Matched metadata']
}

export default function EmailInbox() {
  const [threads, setThreads] = useState([])
  const [messages, setMessages] = useState([])
  const [threadMessages, setThreadMessages] = useState([])
  const [selectedThread, setSelectedThread] = useState(null)
  const [search, setSearch] = useState('')
  const [labels, setLabels] = useState([])
  const [filter, setFilter] = useState('all')
  const [searchResults, setSearchResults] = useState([])
  const [isSearching, setIsSearching] = useState(false)
  const [selectedMessageId, setSelectedMessageId] = useState(null)
  const [attachments, setAttachments] = useState([])

  const loadThreads = async () => {
    try {
      const data = await apiFetch('/api/email/threads')
      if (Array.isArray(data)) {
        setThreads(data)
        setSelectedThread(data[0]?.id || null)
      }
      const allMessages = await apiFetch('/api/email/messages')
      if (Array.isArray(allMessages)) {
        setThreadMessages(allMessages)
      }
    } catch (error) {
      // handled globally
    }
  }

  const loadLabels = async () => {
    try {
      const data = await apiFetch('/api/email/labels')
      if (Array.isArray(data)) {
        setLabels(data)
      }
    } catch (error) {
      // handled globally
    }
  }

  const loadMessages = async (threadId) => {
    if (!threadId) {
      setMessages([])
      return
    }
    try {
      const data = await apiFetch(`/api/email/messages?thread_id=${threadId}`)
      if (Array.isArray(data)) {
        setMessages(data)
        setSelectedMessageId(data[data.length - 1]?.id || null)
      }
    } catch (error) {
      // handled globally
    }
  }

  const runSearch = async () => {
    if (!search) {
      setIsSearching(false)
      setSearchResults([])
      loadThreads()
      return
    }
    setIsSearching(true)
    try {
      const params = new URLSearchParams({
        q: search,
        label: filter === 'all' ? '' : filter,
        has_attachments: filter === 'attachments' ? 'true' : '',
      })
      const data = await apiFetch(`/api/email/search?${params.toString()}`)
      if (Array.isArray(data)) {
        setSearchResults(data)
      }
    } catch (error) {
      // handled globally
    }
  }

  useEffect(() => {
    loadThreads()
    loadLabels()
  }, [])

  useEffect(() => {
    loadMessages(selectedThread)
  }, [selectedThread])

  useEffect(() => {
    const loadAttachments = async () => {
      if (!selectedMessageId) {
        setAttachments([])
        return
      }
      try {
        const data = await apiFetch(`/api/email/messages/${selectedMessageId}/attachments`)
        if (Array.isArray(data)) {
          setAttachments(data)
        }
      } catch (error) {
        // handled globally
      }
    }
    loadAttachments()
  }, [selectedMessageId])

  useEffect(() => {
    const handler = (event) => {
      const tag = event.target?.tagName?.toLowerCase()
      if (tag === 'input' || tag === 'textarea') {
        return
      }
      if (event.key === 'e') {
        handleArchive()
      }
      if (event.key === 'l') {
        handleLabel('legal')
      }
      if (event.key === 'b') {
        handleLabel('billing')
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [activeMessages])

  const mergedLabels = useMemo(() => {
    const existing = labels.map((label) => ({
      slug: label.slug,
      name: label.name,
      color: label.color || 'orange',
    }))
    const registry = [...SYSTEM_LABELS]
    existing.forEach((label) => {
      if (!registry.find((item) => item.slug === label.slug)) {
        registry.push(label)
      }
    })
    return registry
  }, [labels])

  const threadPreview = useMemo(() => {
    const map = {}
    threadMessages.forEach((message) => {
      if (!map[message.thread_id]) {
        map[message.thread_id] = []
      }
      map[message.thread_id].push(message)
    })
    return threads.map((thread) => {
      const threadMessages = map[thread.id] || []
      const lastMessage = threadMessages[threadMessages.length - 1]
      return {
        ...thread,
        lastMessage,
        preview: lastMessage?.body_plain?.slice(0, 120) || 'No messages yet.',
      }
    })
  }, [threads, threadMessages])

  const activeMessages = useMemo(() => {
    if (isSearching) {
      return searchResults
    }
    return messages
  }, [isSearching, searchResults, messages])

  const activeMessage = useMemo(
    () => activeMessages.find((message) => message.id === selectedMessageId) || activeMessages[0],
    [activeMessages, selectedMessageId]
  )

  const handleArchive = async () => {
    if (!activeMessages.length) {
      return
    }
    await Promise.all(
      activeMessages.map((message) =>
        apiFetch(`/api/email/messages/${message.id}/archive`, { method: 'POST' })
      )
    )
    await loadThreads()
    await loadMessages(selectedThread)
  }

  const handleLabel = async (labelSlug) => {
    if (!activeMessages.length) {
      return
    }
    await Promise.all(
      activeMessages.map((message) =>
        apiFetch(`/api/email/messages/${message.id}/labels`, {
          method: 'POST',
          body: JSON.stringify({ label: labelSlug }),
        })
      )
    )
    await loadLabels()
  }

  return (
    <div className="page email-page">
      <SectionHeader
        eyebrow="Quantum Email"
        title="Command Inbox"
        action={<button className="primary-button">Compose</button>}
      />

      <div className="email-shell">
        <aside className="email-rail">
          <div className="email-search">
            <input
              className="text-input"
              placeholder="Search everything (subject, sender, body)"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
            />
            <button className="ghost-button" type="button" onClick={runSearch}>
              Search
            </button>
          </div>

          <div className="email-filters">
            {QUICK_FILTERS.map((chip) => (
              <button
                key={chip.key}
                type="button"
                className={`chip ${filter === chip.key ? 'active' : ''}`}
                onClick={() => setFilter(chip.key)}
              >
                {chip.label}
              </button>
            ))}
          </div>

          <div className="email-labels">
            <p className="eyebrow">System Labels</p>
            <div className="label-list">
              {mergedLabels.map((label) => (
                <button
                  key={label.slug}
                  type="button"
                  className="label-chip"
                  onClick={() => handleLabel(label.slug)}
                >
                  <span className={`label-dot ${label.color || 'orange'}`} />
                  {label.name}
                </button>
              ))}
            </div>
          </div>

          <div className="email-guidance">
            <p className="eyebrow">Inbox Guidance</p>
            <div className="note-card">
              <p className="note-title">Search-first workflow</p>
              <p className="note-body">
                Start with a search or label filter. Threads update instantly as routing rules run.
              </p>
            </div>
            <div className="note-card">
              <p className="note-title">Compliance watch</p>
              <p className="note-body">
                Legal holds and retention policies apply on every archive, delete, and export action.
              </p>
            </div>
          </div>
        </aside>

        <section className="email-center">
          <div className="email-center-header">
            <div>
              <p className="eyebrow">Threads</p>
              <h2>{isSearching ? 'Search Results' : 'Inbox Threads'}</h2>
            </div>
            <div className="email-actions">
              <button className="ghost-button" type="button" onClick={handleArchive}>
                Archive Thread
              </button>
              <button className="ghost-button" type="button" onClick={() => handleLabel('billing')}>
                Label Billing
              </button>
              <button className="ghost-button" type="button">
                Escalate
              </button>
            </div>
          </div>

          <div className="email-thread-list">
            {isSearching && !searchResults.length ? (
              <div className="empty-state">
                <h3>No results yet</h3>
                <p>Refine search filters or ingest inbound mail to populate the inbox.</p>
              </div>
            ) : null}
            {!isSearching && !threadPreview.length ? (
              <div className="empty-state">
                <h3>Inbox ready</h3>
                <p>Connect Postmark inbound to populate live threads, labels, and linked records.</p>
              </div>
            ) : null}
            {isSearching
              ? searchResults.map((message) => (
                  <button
                    key={message.id}
                    type="button"
                    className={`email-thread-item ${selectedMessageId === message.id ? 'active' : ''}`}
                    onClick={() => setSelectedMessageId(message.id)}
                  >
                    <div className="thread-main">
                      <p className="thread-title">{message.subject || 'No subject'}</p>
                      <p className="thread-preview">{message.body_plain?.slice(0, 120) || 'No preview'}</p>
                    </div>
                    <div className="thread-meta">
                      <span className="thread-sender">{message.sender || 'Unknown sender'}</span>
                      <span className="thread-reason">{buildMatchReasons(message, search).join(', ')}</span>
                    </div>
                  </button>
                ))
              : threadPreview.map((thread) => (
                  <button
                    key={thread.id}
                    type="button"
                    className={`email-thread-item ${selectedThread === thread.id ? 'active' : ''}`}
                    onClick={() => setSelectedThread(thread.id)}
                  >
                    <div className="thread-main">
                      <p className="thread-title">{thread.subject || 'No subject'}</p>
                      <p className="thread-preview">{thread.preview}</p>
                    </div>
                    <div className="thread-meta">
                      <span className="thread-sender">{thread.lastMessage?.sender || 'Unassigned'}</span>
                      <span className="thread-status">{thread.status || 'open'}</span>
                    </div>
                  </button>
                ))}
          </div>

          <div className="email-thread-detail">
            <div className="thread-actions">
              <button className="primary-button" type="button">
                Reply
              </button>
              <button className="ghost-button" type="button">
                Reply All
              </button>
              <button className="ghost-button" type="button">
                Forward
              </button>
              <button className="ghost-button" type="button">
                Export
              </button>
            </div>
            <div className="thread-timeline">
              {activeMessages.length > 0 ? (
                activeMessages.map((message) => (
                  <div key={message.id} className="email-message-card">
                    <div className="email-message-meta">
                      <div>
                        <p className="note-title">{message.sender || 'Unknown sender'}</p>
                        <p className="note-body">{message.subject || 'No subject'}</p>
                      </div>
                      <StatusBadge value={message.status || 'received'} />
                    </div>
                    <p className="email-message-body">{message.body_plain || 'No body text available.'}</p>
                  </div>
                ))
              ) : (
                <div className="empty-state">
                  <h3>Thread context</h3>
                  <p>Select a thread to see the full conversation timeline.</p>
                </div>
              )}
            </div>
          </div>
        </section>

        <aside className="email-context">
          <AdvisoryPanel
            title="Command Context"
            model="email-intel"
            version="1.0"
            level="ADVISORY"
            message="Deterministic rules classify every message, apply labels, and enforce retention."
            reason="Rules-first intelligence"
          />
          <div className="note-card">
            <p className="note-title">Thread summary</p>
            <p className="note-body">
              {activeMessage
                ? 'Summary available. Use explain to generate a deterministic overview.'
                : 'Select a thread to generate a summary.'}
            </p>
          </div>
          <div className="note-card">
            <p className="note-title">Retention & Legal Hold</p>
            <p className="note-body">
              Holds and retention are enforced on archive/delete/export. Rule IDs:
              EMAIL.RETENTION.BLOCK_DELETE.v1, EMAIL.LEGAL_HOLD.BLOCK.v1.
            </p>
          </div>
          <div className="note-card">
            <p className="note-title">Allowed Actions</p>
            <p className="note-body">
              Reply, label, archive, and export are available. Blocked actions return a DecisionPacket
              with rule IDs and next steps.
            </p>
          </div>
          <div className="note-card">
            <p className="note-title">Linked records</p>
            <p className="note-body">
              Linked billing cases, legal holds, and documents surface here once attached.
            </p>
          </div>
          <div className="note-card">
            <p className="note-title">Attachments</p>
            {attachments.length > 0 ? (
              <ul className="tight-list">
                {attachments.map((item) => (
                  <li key={item.id}>
                    {item.filename} ({item.content_type || 'file'})
                  </li>
                ))}
              </ul>
            ) : (
              <p className="note-body">No attachments linked yet.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  )
}
