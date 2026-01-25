import { useEffect, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import AdvisoryPanel from '../components/AdvisoryPanel.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

const accountColumns = [
  { key: 'patient_name', label: 'Patient' },
  { key: 'email', label: 'Email' },
  { key: 'status', label: 'Status' },
]

const messageColumns = [
  { key: 'account_id', label: 'Account' },
  { key: 'sender', label: 'Sender' },
  { key: 'message', label: 'Message' },
  { key: 'status', label: 'Status' },
]

export default function PatientPortal() {
  const [invoiceRows, setInvoiceRows] = useState([])
  const [invoiceLoading, setInvoiceLoading] = useState(true)
  const [activeCheckout, setActiveCheckout] = useState(null)
  const [accountRows, setAccountRows] = useState([])
  const [messageRows, setMessageRows] = useState([])

  useEffect(() => {
    let mounted = true
    const loadInvoices = async () => {
      try {
        const [invoiceData, accountData, messageData] = await Promise.all([
          apiFetch('/api/billing/invoices'),
          apiFetch('/api/billing/patient/accounts'),
          apiFetch('/api/comms/threads'),
        ])
        if (mounted && Array.isArray(invoiceData)) {
          setInvoiceRows(invoiceData)
        }
        if (mounted && Array.isArray(accountData)) {
          setAccountRows(accountData)
        }
        if (mounted && Array.isArray(messageData)) {
          setMessageRows(messageData)
        }
      } catch (err) {
        if (mounted) {
          setInvoiceRows([])
          setAccountRows([])
          setMessageRows([])
        }
      } finally {
        if (mounted) {
          setInvoiceLoading(false)
        }
      }
    }
    loadInvoices()
    return () => {
      mounted = false
    }
  }, [])

  const formatCurrency = (amount, currency = 'USD') => {
    const normalized = Number.isFinite(Number(amount)) ? Number(amount) / 100 : 0
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(normalized)
  }

  const handleCheckout = async (invoice) => {
    if (!invoice?.id || activeCheckout) {
      return
    }
    setActiveCheckout(invoice.id)
    try {
      const session = await apiFetch('/api/payments/stripe/checkout', {
        method: 'POST',
        body: JSON.stringify({
          invoiceId: invoice.id,
        }),
      })
      if (session?.checkoutUrl) {
        window.location.assign(session.checkoutUrl)
        return
      }
    } catch (err) {
      // Error banner handled globally.
    }
    setActiveCheckout(null)
  }

  const invoiceColumns = [
    { key: 'invoice_number', label: 'Invoice' },
    {
      key: 'patient_name',
      label: 'Patient',
      render: (row) => row.meta_data?.patient_name || row.customer_id || 'Unknown',
    },
    {
      key: 'amount_due',
      label: 'Balance',
      render: (row) => formatCurrency(row.amount_due, row.currency || 'USD'),
    },
    {
      key: 'status',
      label: 'Status',
      render: (row) => <StatusBadge value={row.status || 'Open'} />,
    },
    {
      key: 'action',
      label: 'Action',
      render: (row) => (
        <button
          className="table-action"
          disabled={activeCheckout === row.id || row.amount_due <= 0}
          onClick={() => handleCheckout(row)}
        >
          {activeCheckout === row.id ? 'Redirecting…' : 'Pay Now'}
        </button>
      ),
    },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Patient Portal"
        title="Statements, Messages, Records"
      />

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Accounts" title="Portal Access" />
          <DataTable columns={accountColumns} rows={accountRows} emptyState="No accounts." />
        </div>
        <div className="panel">
          <AdvisoryPanel
            title="Patient Support"
            model="patient-assist"
            version="1.0"
            level="ADVISORY"
            message={`${messageRows.length} billing message${messageRows.length === 1 ? '' : 's'} awaiting response.`}
            reason="Portal inbox"
          />
          <div className="note-card">
            <p className="note-title">Payments</p>
            <p className="note-body">
              Patient checkout is ready. {invoiceLoading ? 'Syncing balances…' : 'Balances ready.'}
            </p>
          </div>
        </div>
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Statements" title="Patient Balances" />
        <DataTable
          columns={invoiceColumns}
          rows={invoiceRows}
          emptyState="No patient invoices. Post an adjudicated balance to enable payment."
        />
      </div>

      <div className="panel">
        <SectionHeader eyebrow="Messages" title="Patient Inbox" />
        <DataTable columns={messageColumns} rows={messageRows} emptyState="No messages." />
      </div>
    </div>
  )
}
