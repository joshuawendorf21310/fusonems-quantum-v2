import SectionHeader from '../SectionHeader.jsx'
import StatusBadge from '../StatusBadge.jsx'

export default function InvoiceDetails({ invoice }) {
  if (!invoice) {
    return (
      <div className="panel">
        <SectionHeader eyebrow="Invoice Details" title="Select an invoice" />
      </div>
    )
  }

  return (
    <div className="panel">
      <SectionHeader eyebrow="Invoice Details" title={invoice.invoice_number} />
      <div className="stack">
        <div className="list-row">
          <div>
            <p className="list-title">Status</p>
            <p className="list-sub">{invoice.status}</p>
          </div>
          <StatusBadge value={invoice.status} />
        </div>
        <div className="list-row">
          <div>
            <p className="list-title">Amount Due</p>
            <p className="list-sub">${(invoice.amount_due / 100).toFixed(2)}</p>
          </div>
          <div>
            <p className="list-title">Currency</p>
            <p className="list-sub">{invoice.currency?.toUpperCase()}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
