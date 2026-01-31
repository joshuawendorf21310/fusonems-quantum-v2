"use client"

import { useEffect, useState } from "react"
import { apiFetch } from "@/lib/api"

type FaxStats = {
  sent_today: number
  received_today: number
  failed_24h: number
  pending: number
  weekly_volume: number
  success_rate: number
  provider_status: string
}

type FaxRecord = {
  id: number
  direction: string
  status: string
  sender_number: string
  sender_name: string
  recipient_number: string
  recipient_name: string
  page_count: number
  has_cover_page: boolean
  document_url: string
  provider_fax_id: string
  retry_count: number
  max_retries: number
  error_message: string
  created_at: string
  sent_at?: string
  delivered_at?: string
  failed_at?: string
}

type SendFaxForm = {
  recipient_number: string
  recipient_name: string
  cover_page_enabled: boolean
  cover_page_subject: string
  cover_page_message: string
  cover_page_from: string
  document_file?: File
}

export function FaxDashboardWidget() {
  const [faxStats, setFaxStats] = useState<FaxStats | null>(null)
  const [recentFaxes, setRecentFaxes] = useState<FaxRecord[]>([])
  const [failedFaxes, setFailedFaxes] = useState<FaxRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'overview' | 'inbox' | 'outbox' | 'send'>('overview')
  const [inbox, setInbox] = useState<FaxRecord[]>([])
  const [outbox, setOutbox] = useState<FaxRecord[]>([])
  const [sendForm, setSendForm] = useState<SendFaxForm>({
    recipient_number: "",
    recipient_name: "",
    cover_page_enabled: true,
    cover_page_subject: "",
    cover_page_message: "",
    cover_page_from: "",
    document_file: undefined
  })
  const [sending, setSending] = useState(false)

  useEffect(() => {
    let mounted = true
    
    const fetchData = () => {
      // Fetch fax stats
      apiFetch<{stats: FaxStats}>("/api/founder/fax/stats")
        .then(data => {
          if (mounted) setFaxStats(data.stats)
        })
        .catch(() => mounted && setFaxStats(null))
      
      // Fetch recent faxes
      apiFetch<{faxes: FaxRecord[]}>("/api/founder/fax/recent?limit=15")
        .then(data => {
          if (mounted) setRecentFaxes(data.faxes)
        })
        .catch(() => mounted && setRecentFaxes([]))
      
      // Fetch failed faxes
      apiFetch<{faxes: FaxRecord[]}>("/api/founder/fax/failed?limit=10")
        .then(data => {
          if (mounted) setFailedFaxes(data.faxes)
        })
        .catch(() => mounted && setFailedFaxes([]))
      
      setLoading(false)
    }
    
    fetchData()
    const interval = setInterval(fetchData, 60000)  // Every 60s
    
    return () => {
      mounted = false
      clearInterval(interval)
    }
  }, [])

  const fetchInbox = () => {
    apiFetch<{faxes: FaxRecord[]}>("/api/founder/fax/inbox?limit=20")
      .then(data => setInbox(data.faxes))
      .catch(() => setInbox([]))
  }

  const fetchOutbox = () => {
    apiFetch<{faxes: FaxRecord[]}>("/api/founder/fax/outbox?limit=20")
      .then(data => setOutbox(data.faxes))
      .catch(() => setOutbox([]))
  }

  useEffect(() => {
    if (activeTab === 'inbox') {
      fetchInbox()
    } else if (activeTab === 'outbox') {
      fetchOutbox()
    }
  }, [activeTab])

  const handleSendFax = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!sendForm.recipient_number || !sendForm.document_file) {
      alert('Please provide recipient number and document')
      return
    }
    
    setSending(true)
    
    try {
      const formData = new FormData()
      formData.append('recipient_number', sendForm.recipient_number)
      formData.append('recipient_name', sendForm.recipient_name)
      formData.append('cover_page_enabled', sendForm.cover_page_enabled.toString())
      formData.append('cover_page_subject', sendForm.cover_page_subject)
      formData.append('cover_page_message', sendForm.cover_page_message)
      formData.append('cover_page_from', sendForm.cover_page_from)
      formData.append('file', sendForm.document_file)
      
      const response = await fetch('/api/founder/fax/send/upload', {
        method: 'POST',
        body: formData,
        credentials: 'include'
      })
      
      const result = await response.json()
      
      if (result.success) {
        alert('Fax sent successfully!')
        setSendForm({
          recipient_number: "",
          recipient_name: "",
          cover_page_enabled: true,
          cover_page_subject: "",
          cover_page_message: "",
          cover_page_from: "",
          document_file: undefined
        })
        setActiveTab('overview')
        // Refresh data
        window.location.reload()
      } else {
        alert(`Failed to send fax: ${result.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error sending fax:', error)
      alert('Error sending fax')
    } finally {
      setSending(false)
    }
  }

  const handleRetryFax = async (faxId: number) => {
    if (!confirm('Retry this failed fax?')) return
    
    try {
      const response = await apiFetch(`/api/founder/fax/${faxId}/retry`, {
        method: 'POST'
      })
      
      if (response.success) {
        alert('Fax retry initiated!')
        window.location.reload()
      } else {
        alert(`Failed to retry: ${response.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error retrying fax:', error)
      alert('Error retrying fax')
    }
  }

  const handleDeleteFax = async (faxId: number) => {
    if (!confirm('Delete this fax record?')) return
    
    try {
      const response = await apiFetch(`/api/founder/fax/${faxId}`, {
        method: 'DELETE'
      })
      
      if (response.success) {
        alert('Fax deleted!')
        window.location.reload()
      } else {
        alert('Failed to delete fax')
      }
    } catch (error) {
      console.error('Error deleting fax:', error)
      alert('Error deleting fax')
    }
  }

  const getStatusBadge = (status: string) => {
    const badges = {
      'queued': 'bg-yellow-100 text-yellow-800',
      'sending': 'bg-blue-100 text-blue-800',
      'delivered': 'bg-green-100 text-green-800',
      'failed': 'bg-red-100 text-red-800',
      'received': 'bg-purple-100 text-purple-800'
    }
    return badges[status as keyof typeof badges] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-24 bg-gray-200 rounded mb-4"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-lg">
      <div className="border-b border-gray-200 p-6">
        <h2 className="text-2xl font-bold text-gray-900">Fax Communications</h2>
        <p className="mt-1 text-sm text-gray-600">Healthcare fax management and tracking</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex -mb-px">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-4 px-6 text-sm font-medium border-b-2 ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('inbox')}
            className={`py-4 px-6 text-sm font-medium border-b-2 ${
              activeTab === 'inbox'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Inbox
          </button>
          <button
            onClick={() => setActiveTab('outbox')}
            className={`py-4 px-6 text-sm font-medium border-b-2 ${
              activeTab === 'outbox'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Outbox
          </button>
          <button
            onClick={() => setActiveTab('send')}
            className={`py-4 px-6 text-sm font-medium border-b-2 ${
              activeTab === 'send'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Send Fax
          </button>
        </nav>
      </div>

      <div className="p-6">
        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="text-sm font-medium text-blue-600">Sent Today</div>
                <div className="mt-2 text-3xl font-bold text-blue-900">{faxStats?.sent_today || 0}</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-4">
                <div className="text-sm font-medium text-purple-600">Received Today</div>
                <div className="mt-2 text-3xl font-bold text-purple-900">{faxStats?.received_today || 0}</div>
              </div>
              <div className="bg-yellow-50 rounded-lg p-4">
                <div className="text-sm font-medium text-yellow-600">Pending</div>
                <div className="mt-2 text-3xl font-bold text-yellow-900">{faxStats?.pending || 0}</div>
              </div>
              <div className="bg-red-50 rounded-lg p-4">
                <div className="text-sm font-medium text-red-600">Failed (24h)</div>
                <div className="mt-2 text-3xl font-bold text-red-900">{faxStats?.failed_24h || 0}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-4">
                <div className="text-sm font-medium text-green-600">Success Rate</div>
                <div className="mt-2 text-3xl font-bold text-green-900">{faxStats?.success_rate || 0}%</div>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="text-sm font-medium text-gray-600">Weekly Volume</div>
                <div className="mt-2 text-3xl font-bold text-gray-900">{faxStats?.weekly_volume || 0}</div>
              </div>
            </div>

            {/* Failed Faxes Alert */}
            {failedFaxes.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-red-900">Failed Faxes Need Attention</h3>
                  <span className="bg-red-600 text-white px-3 py-1 rounded-full text-sm font-bold">
                    {failedFaxes.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {failedFaxes.map(fax => (
                    <div key={fax.id} className="bg-white rounded p-3 flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">
                          {fax.direction === 'outbound' ? `To: ${fax.recipient_number}` : `From: ${fax.sender_number}`}
                        </div>
                        <div className="text-sm text-red-600">{fax.error_message}</div>
                        <div className="text-xs text-gray-500">Retry {fax.retry_count}/{fax.max_retries}</div>
                      </div>
                      <button
                        onClick={() => handleRetryFax(fax.id)}
                        className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 text-sm font-medium"
                      >
                        Retry Now
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent Activity */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">Recent Fax Activity</h3>
              <div className="space-y-2">
                {recentFaxes.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">No recent fax activity</div>
                ) : (
                  recentFaxes.map(fax => (
                    <div key={fax.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(fax.status)}`}>
                              {fax.status.toUpperCase()}
                            </span>
                            <span className="text-sm font-medium text-gray-900">
                              {fax.direction === 'outbound' ? '→' : '←'} 
                              {fax.direction === 'outbound' ? fax.recipient_number : fax.sender_number}
                            </span>
                            {fax.recipient_name && (
                              <span className="text-sm text-gray-600">({fax.recipient_name})</span>
                            )}
                          </div>
                          <div className="mt-1 text-xs text-gray-500">
                            {fax.page_count} pages • {formatDate(fax.created_at)}
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {fax.document_url && (
                            <a
                              href={fax.document_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                            >
                              View
                            </a>
                          )}
                          <button
                            onClick={() => handleDeleteFax(fax.id)}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        )}

        {/* Inbox Tab */}
        {activeTab === 'inbox' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Received Faxes</h3>
            {inbox.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No received faxes</div>
            ) : (
              <div className="space-y-2">
                {inbox.map(fax => (
                  <div key={fax.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-medium text-gray-900">From: {fax.sender_number}</div>
                        {fax.sender_name && <div className="text-sm text-gray-600">{fax.sender_name}</div>}
                        <div className="text-xs text-gray-500 mt-1">
                          {fax.page_count} pages • {formatDate(fax.created_at)}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {fax.document_url && (
                          <a
                            href={fax.document_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 text-sm"
                          >
                            View Document
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Outbox Tab */}
        {activeTab === 'outbox' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Sent Faxes</h3>
            {outbox.length === 0 ? (
              <div className="text-center py-8 text-gray-500">No sent faxes</div>
            ) : (
              <div className="space-y-2">
                {outbox.map(fax => (
                  <div key={fax.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-3">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadge(fax.status)}`}>
                            {fax.status.toUpperCase()}
                          </span>
                          <span className="font-medium text-gray-900">To: {fax.recipient_number}</span>
                        </div>
                        {fax.recipient_name && <div className="text-sm text-gray-600 mt-1">{fax.recipient_name}</div>}
                        <div className="text-xs text-gray-500 mt-1">
                          {fax.page_count} pages • Sent: {formatDate(fax.sent_at)} • Delivered: {formatDate(fax.delivered_at)}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        {fax.status === 'failed' && fax.retry_count < fax.max_retries && (
                          <button
                            onClick={() => handleRetryFax(fax.id)}
                            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 text-sm"
                          >
                            Retry
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Send Fax Tab */}
        {activeTab === 'send' && (
          <form onSubmit={handleSendFax} className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-900">Send New Fax</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Recipient Fax Number *
                </label>
                <input
                  type="tel"
                  value={sendForm.recipient_number}
                  onChange={(e) => setSendForm({...sendForm, recipient_number: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="+1234567890"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Recipient Name
                </label>
                <input
                  type="text"
                  value={sendForm.recipient_name}
                  onChange={(e) => setSendForm({...sendForm, recipient_name: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="Dr. Smith"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Document to Fax *
              </label>
              <input
                type="file"
                accept=".pdf,image/png,image/jpeg,image/tiff"
                onChange={(e) => setSendForm({...sendForm, document_file: e.target.files?.[0]})}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="mt-1 text-xs text-gray-500">Supported: PDF, PNG, JPEG, TIFF</p>
            </div>

            <div className="border-t border-gray-200 pt-6">
              <div className="flex items-center gap-3 mb-4">
                <input
                  type="checkbox"
                  id="cover_page"
                  checked={sendForm.cover_page_enabled}
                  onChange={(e) => setSendForm({...sendForm, cover_page_enabled: e.target.checked})}
                  className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                />
                <label htmlFor="cover_page" className="text-sm font-medium text-gray-700">
                  Include Cover Page
                </label>
              </div>

              {sendForm.cover_page_enabled && (
                <div className="space-y-4 pl-7">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Subject
                    </label>
                    <input
                      type="text"
                      value={sendForm.cover_page_subject}
                      onChange={(e) => setSendForm({...sendForm, cover_page_subject: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Medical Records Request"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Message
                    </label>
                    <textarea
                      value={sendForm.cover_page_message}
                      onChange={(e) => setSendForm({...sendForm, cover_page_message: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      rows={4}
                      placeholder="Please find attached medical records..."
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      From Name
                    </label>
                    <input
                      type="text"
                      value={sendForm.cover_page_from}
                      onChange={(e) => setSendForm({...sendForm, cover_page_from: e.target.value})}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      placeholder="Your Name"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-4">
              <button
                type="submit"
                disabled={sending}
                className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-medium disabled:bg-gray-400"
              >
                {sending ? 'Sending...' : 'Send Fax'}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('overview')}
                className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
