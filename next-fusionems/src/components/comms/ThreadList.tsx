import { CommsThread } from '../../lib/comms/types'
import StatusBadge from './StatusBadge'

type ThreadListProps = {
  threads: CommsThread[]
  selectedThreadId: string | null
  onSelect: (threadId: string) => void
  status: 'idle' | 'loading' | 'error'
}

export default function ThreadList({ threads, selectedThreadId, onSelect, status }: ThreadListProps) {
  if (status === 'loading') {
    return <p className="empty-state">Loading threads…</p>
  }

  if (status === 'error') {
    return <p className="empty-state">Unable to load communications threads.</p>
  }

  if (!threads.length) {
    return <p className="empty-state">No conversations available.</p>
  }

  return (
    <div className="thread-list">
      {threads.map((thread) => (
        <button
          key={thread.id}
          type="button"
          className={`thread-card ${selectedThreadId === thread.id ? 'thread-card-active' : ''}`}
          onClick={() => onSelect(thread.id)}
        >
          <div className="thread-card-header">
            <h4>{thread.subject || thread.preview}</h4>
            <StatusBadge status={thread.status} />
          </div>
          <p className="thread-preview">{thread.preview}</p>
          <div className="thread-meta">
            <span>{thread.channel.toUpperCase()}</span>
            <span>{thread.unreadCount} unread</span>
          </div>
        </button>
      ))}
    </div>
  )
}
