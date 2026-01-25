import { CommsMessage } from '../../lib/comms/types'

type AttachmentListProps = {
  messages: CommsMessage[]
}

export default function AttachmentList({ messages }: AttachmentListProps) {
  const attachments = messages.flatMap((message) =>
    message.attachments.map((attachment) => ({
      ...attachment,
      messageId: message.id,
    }))
  )

  if (!attachments.length) {
    return null
  }

  return (
    <section className="panel attachment-panel">
      <h4>Attachments</h4>
      <ul>
        {attachments.map((attachment) => (
          <li key={`${attachment.messageId}-${attachment.id}`}>
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
    </section>
  )
}
