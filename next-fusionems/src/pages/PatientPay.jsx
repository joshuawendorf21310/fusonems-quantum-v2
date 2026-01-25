import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import { apiFetch } from '../services/api.js'

export default function PatientPay() {
  const { token } = useParams()
  const [invoice, setInvoice] = useState(null)
  const [items, setItems] = useState([])
  const [documents, setDocuments] = useState([])
  const [payments, setPayments] = useState([])

  useEffect(() => {
    if (!token) return
    apiFetch(`/api/billing/portal/${token}`).then((data) => {
      setInvoice(data.invoice)
      setItems(Array.isArray(data.items) ? data.items : [])
      setDocuments(Array.isArray(data.documents) ? data.documents : [])
      setPayments(Array.isArray(data.payments) ? data.payments : [])
    })
  }, [token])

  const itemColumns = [
    { key: 'description', label: 'Description' },
    { key: 'quantity', label: 'Qty' },
    { key: 'amount', label: 'Amount', render: (row) => `$${(row.amount / 100).toFixed(2)}` },
  ]

  const paymentColumns = [
    { key: 'provider', label: 'Provider' },
    { key: 'amount', label: 'Amount', render: (row) => `$${(row.amount / 100).toFixed(2)}` },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const handlePay = async () => {
    const response = await apiFetch('/api/payments/stripe/portal-checkout', {
      method: 'POST',
      body: JSON.stringify({ token }),
    })
    if (response?.checkoutUrl) {
      window.location.assign(response.checkoutUrl)
    }
  }

  return (
    <div className="page">
      <SectionHeader eyebrow="Patient Billing" title="Secure Payment" />
      {invoice ? (
        <div className="section-grid">
          <div className="panel">
            <SectionHeader eyebrow="Invoice" title={invoice.invoice_number} />
            <div className="stack">
              <div className="list-row">
                <div>
                  <p className="list-title">Balance Due</p>
                  <p className="list-sub">${(invoice.amount_due / 100).toFixed(2)}</p>
                </div>
                <StatusBadge value={invoice.status} />
              </div>
              <button className="primary-button" onClick={handlePay}>
                Pay with Stripe
              </button>
            </div>
          </div>
          <div className="panel">
            <SectionHeader eyebrow="Documents" title="Download" />
            <div className="stack">
              {documents.length === 0 ? (
                <p className="list-sub">No documents available.</p>
              ) : (
                documents.map((doc) => (
                  <a
                    key={doc.id}
                    className="ghost-button"
                    href={`/api/billing/portal/${token}/documents/${doc.id}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {doc.doc_type.toUpperCase()} PDF
                  </a>
                ))
              )}
            </div>
          </div>
        </div>
      ) : (
        <div className="panel">
          <p className="list-sub">Loading invoice...</p>
        </div>
      )}

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Line Items" title="Invoice Summary" />
          <DataTable columns={itemColumns} rows={items} emptyState="No line items." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Payments" title="Payment History" />
          <DataTable columns={paymentColumns} rows={payments} emptyState="No payments recorded." />
        </div>
      </div>
    </div>
  )
}
