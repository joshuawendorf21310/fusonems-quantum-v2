import { useEffect, useMemo, useState } from 'react'
import SectionHeader from '../components/SectionHeader.jsx'
import BillingReports from '../components/billing/BillingReports.jsx'
import { apiFetch } from '../services/api.js'

export default function FounderBillingReports() {
  const [invoices, setInvoices] = useState([])
  const [denials, setDenials] = useState([])

  useEffect(() => {
    const load = async () => {
      const [invoiceData, denialData] = await Promise.all([
        apiFetch('/api/billing/invoices'),
        apiFetch('/api/billing/denials'),
      ])
      setInvoices(Array.isArray(invoiceData) ? invoiceData : [])
      setDenials(Array.isArray(denialData) ? denialData : [])
    }
    load()
  }, [])

  const metrics = useMemo(() => {
    const openInvoices = invoices.filter((invoice) => invoice.status !== 'PAID').length
    const totalAr = invoices.reduce((sum, invoice) => sum + (invoice.amount_due || 0), 0)
    return { openInvoices, totalAr, denials: denials.length }
  }, [invoices, denials])

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Billing" title="Reports" />
      <BillingReports metrics={metrics} />
    </div>
  )
}
