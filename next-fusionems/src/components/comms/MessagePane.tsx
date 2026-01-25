import { CommsMessage, CommsThread } from '../../lib/comms/types'
import StatusBadge from './StatusBadge'

type MessagePaneProps = {
  thread: CommsThread | null
  messages: CommsMessage[]
  onCall: () => void
}

export default function MessagePane({ thread, messages, onCall }: MessagePaneProps) {
  if (!thread) {
    return <div className="panel empty-state">Select a conversation to view details.</div>
  }

  return (
    <section className="panel message-pane">
      <header className="message-pane-header">
        <div>
          <h3>{thread.subject || 'Conversation'}</h3>
          <p className="muted">{thread.participants.map((p) => p.name || p.address).join(', ')}</p>
        </div>
        <div className="message-pane-actions">
          <StatusBadge status={thread.status} />
          <button className="ghost-button" type="button" onClick={onCall}>
            Call
          </button>
        </div>
      </header>
      <div className="message-list">
        {messages.map((message) => (
          <article key={message.id} className="message-card">
            <header className="message-card-header">
              <div>
                <strong>{message.sender.name || message.sender.address}</strong>
                <span className="muted"> · {message.channel.toUpperCase()}</span>
              </div>
              <span className="muted">{new Date(message.createdAt).toLocaleString()}</span>
            </header>
            <p>{message.body}</p>
            {message.attachments.length > 0 && (
              <ul className="attachment-list">
                {message.attachments.map((attachment) => (
                  <li key={attachment.id}>
                    {attachment.url ? (
                      <a href={attachment.url} target="_blank" rel="noreferrer">
                        {attachment.filename}
                      </a>
                    ) : (
                      attachment.filename
                    )}
                  </li>
                ))}
              </ul>
            )}
          </article>
        ))}
        {!messages.length && <p className="empty-state">No messages in this thread.</p>}
      </div>
    </section>
  )
}
