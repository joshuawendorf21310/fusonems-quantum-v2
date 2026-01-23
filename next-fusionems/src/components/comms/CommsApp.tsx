import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  CommsAttachment,
  CommsMessage,
  CommsSearchFilters,
  CommsThread,
} from '../../lib/comms/types'
import {
  initiateCall,
  listMessages,
  listThreads,
  sendEmail,
  sendFax,
  sendSms,
} from '../../services/comms/api'
import { subscribeToThreads } from '../../services/comms/realtime'
import AttachmentList from './AttachmentList'
import ComposeModal from './ComposeModal'
import FiltersBar from './FiltersBar'
import MessagePane from './MessagePane'
import SearchBar from './SearchBar'
import ThreadList from './ThreadList'

export default function CommsApp() {
  const [threads, setThreads] = useState<CommsThread[]>([])
  const [messages, setMessages] = useState<CommsMessage[]>([])
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [filters, setFilters] = useState<CommsSearchFilters>({ channel: 'all' })
  const [searchQuery, setSearchQuery] = useState('')
  const [isComposeOpen, setIsComposeOpen] = useState(false)
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')

  const activeThread = useMemo(
    () => threads.find((thread) => thread.id === selectedThreadId) ?? null,
    [threads, selectedThreadId]
  )

  const refreshThreads = useCallback(async () => {
    setStatus('loading')
    try {
      const updated = await listThreads({ ...filters, query: searchQuery || undefined })
      setThreads(updated)
      setStatus('idle')
    } catch (error) {
      console.error('Failed to load threads', error)
      setStatus('error')
    }
  }, [filters, searchQuery])

  const refreshMessages = useCallback(async () => {
    if (!selectedThreadId) {
      setMessages([])
      return
    }
    try {
      const data = await listMessages(selectedThreadId)
      setMessages(data)
    } catch (error) {
      console.error('Failed to load messages', error)
    }
  }, [selectedThreadId])

  useEffect(() => {
    refreshThreads()
  }, [refreshThreads])

  useEffect(() => {
    const subscription = subscribeToThreads(
      { ...filters, query: searchQuery || undefined },
      setThreads
    )
    return () => subscription.stop()
  }, [filters, searchQuery])

  useEffect(() => {
    refreshMessages()
  }, [refreshMessages])

  const handleSendEmail = useCallback(
    async (payload: { to: string[]; subject: string; body: string; attachments: CommsAttachment[] }) => {
      const response = await sendEmail({
        ...payload,
        threadId: selectedThreadId ?? undefined,
      })
      setMessages((prev) => [...prev, response])
      await refreshThreads()
    },
    [refreshThreads, selectedThreadId]
  )

  const handleSendSms = useCallback(
    async (payload: { to: string; body: string }) => {
      const response = await sendSms({
        ...payload,
        threadId: selectedThreadId ?? undefined,
      })
      setMessages((prev) => [...prev, response])
      await refreshThreads()
    },
    [refreshThreads, selectedThreadId]
  )

  const handleSendFax = useCallback(
    async (payload: { to: string; documentUrl: string }) => {
      const response = await sendFax({
        ...payload,
        threadId: selectedThreadId ?? undefined,
      })
      setMessages((prev) => [...prev, response])
      await refreshThreads()
    },
    [refreshThreads, selectedThreadId]
  )

  const handleCall = useCallback(async () => {
    if (!activeThread) return
    const recipient = activeThread.participants.find((participant) => participant.role === 'recipient')
    if (!recipient) return
    await initiateCall({ to: recipient.address, threadId: activeThread.id })
  }, [activeThread])

  return (
    <section className="page">
      <header className="section-header">
        <div>
          <p className="eyebrow">Communications Hub</p>
          <h2>Unified Communications Center</h2>
        </div>
        <div className="header-actions">
          <button className="primary-button" type="button" onClick={() => setIsComposeOpen(true)}>
            Compose
          </button>
        </div>
      </header>

      <div className="comms-layout">
        <aside className="comms-sidebar">
          <SearchBar value={searchQuery} onChange={setSearchQuery} />
          <FiltersBar filters={filters} onChange={setFilters} />
          <ThreadList
            threads={threads}
            selectedThreadId={selectedThreadId}
            onSelect={setSelectedThreadId}
            status={status}
          />
        </aside>
        <main className="comms-main">
          <MessagePane
            thread={activeThread}
            messages={messages}
            onCall={handleCall}
          />
          <AttachmentList messages={messages} />
        </main>
      </div>

      <ComposeModal
        isOpen={isComposeOpen}
        onClose={() => setIsComposeOpen(false)}
        onSendEmail={handleSendEmail}
        onSendSms={handleSendSms}
        onSendFax={handleSendFax}
      />
    </section>
  )
}
