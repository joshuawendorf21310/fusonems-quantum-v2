import SectionHeader from '../SectionHeader.jsx'
import StatCard from '../StatCard.jsx'

export default function BillingReports({ metrics }) {
  return (
    <div className="panel">
      <SectionHeader eyebrow="Reports" title="Billing Performance" />
      <div className="cards">
        <StatCard title="Open Invoices" value={metrics.openInvoices} />
        <StatCard title="Total AR" value={`$${(metrics.totalAr / 100).toFixed(2)}`} />
        <StatCard title="Denials" value={metrics.denials} />
      </div>
    </div>
  )
}
