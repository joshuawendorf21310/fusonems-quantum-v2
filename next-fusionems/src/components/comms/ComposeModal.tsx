import { useState } from 'react'
import { CommsAttachment } from '../../lib/comms/types'
import { uploadAttachment } from '../../services/comms/api'

type ComposeModalProps = {
  isOpen: boolean
  onClose: () => void
  onSendEmail: (payload: { to: string[]; subject: string; body: string; attachments: CommsAttachment[] }) => Promise<void>
  onSendSms: (payload: { to: string; body: string }) => Promise<void>
  onSendFax: (payload: { to: string; documentUrl: string }) => Promise<void>
}

type Channel = 'email' | 'sms' | 'fax'

export default function ComposeModal({ isOpen, onClose, onSendEmail, onSendSms, onSendFax }: ComposeModalProps) {
  const [channel, setChannel] = useState<Channel>('email')
  const [to, setTo] = useState('')
  const [subject, setSubject] = useState('')
  const [body, setBody] = useState('')
  const [documentUrl, setDocumentUrl] = useState('')
  const [attachments, setAttachments] = useState<CommsAttachment[]>([])
  const [status, setStatus] = useState<'idle' | 'sending' | 'error'>('idle')

  if (!isOpen) return null

  const handleSend = async () => {
    setStatus('sending')
    try {
      if (channel === 'email') {
        await onSendEmail({
          to: to.split(',').map((item) => item.trim()).filter(Boolean),
          subject,
          body,
          attachments,
        })
      } else if (channel === 'sms') {
        await onSendSms({ to, body })
      } else {
        await onSendFax({ to, documentUrl })
      }
      setStatus('idle')
      setTo('')
      setSubject('')
      setBody('')
      setDocumentUrl('')
      setAttachments([])
      onClose()
    } catch (error) {
      console.error('Send failed', error)
      setStatus('error')
    }
  }

  const handleAttachmentUpload = async (files: FileList | null) => {
    if (!files || !files.length) return
    setStatus('sending')
    try {
      const uploaded: CommsAttachment[] = []
      for (const file of Array.from(files)) {
        const attachment = await uploadAttachment(file)
        uploaded.push(attachment)
      }
      setAttachments((prev) => [...prev, ...uploaded])
      if (channel === 'fax' && uploaded[0]?.url) {
        setDocumentUrl(uploaded[0].url)
      }
      setStatus('idle')
    } catch (error) {
      console.error('Attachment upload failed', error)
      setStatus('error')
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <header className="modal-header">
          <h3>Compose Message</h3>
          <button className="ghost-button" type="button" onClick={onClose}>
            Close
          </button>
        </header>
        <div className="modal-body">
          <label>
            Channel
            <select value={channel} onChange={(event) => setChannel(event.target.value as Channel)}>
              <option value="email">Email</option>
              <option value="sms">SMS</option>
              <option value="fax">Fax</option>
            </select>
          </label>
          <label>
            To
            <input value={to} onChange={(event) => setTo(event.target.value)} placeholder="recipient" />
          </label>
          {channel === 'email' && (
            <label>
              Subject
              <input value={subject} onChange={(event) => setSubject(event.target.value)} />
            </label>
          )}
          <label>
            Attachments
            <input type="file" multiple onChange={(event) => handleAttachmentUpload(event.target.files)} />
          </label>
          {attachments.length > 0 && (
            <ul className="attachment-list">
              {attachments.map((attachment) => (
                <li key={attachment.id}>{attachment.filename}</li>
              ))}
            </ul>
          )}
          {channel === 'fax' ? (
            <label>
              Document URL
              <input value={documentUrl} onChange={(event) => setDocumentUrl(event.target.value)} />
            </label>
          ) : (
            <label>
              Body
              <textarea value={body} onChange={(event) => setBody(event.target.value)} rows={6} />
            </label>
          )}
          {status === 'error' && <p className="error-text">Unable to send message.</p>}
        </div>
        <footer className="modal-footer">
          <button className="primary-button" type="button" onClick={handleSend} disabled={status === 'sending'}>
            {status === 'sending' ? 'Sending…' : 'Send'}
          </button>
        </footer>
      </div>
    </div>
  )
}
