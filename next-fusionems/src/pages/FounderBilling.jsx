import { useEffect, useMemo, useState } from 'react'
import { apiFetch } from '../services/api.js'
import SectionHeader from '../components/SectionHeader.jsx'
import BillingSpine from '../components/billing/BillingSpine.jsx'
import ClaimLifecycle from '../components/billing/ClaimLifecycle.jsx'
import DenialAppealEngine from '../components/billing/DenialAppealEngine.jsx'
import FacilityContactSpine from '../components/billing/FacilityContactSpine.jsx'
import BillingReports from '../components/billing/BillingReports.jsx'

export default function FounderBilling() {
  const [invoices, setInvoices] = useState([])
  const [claims, setClaims] = useState([])
  const [denials, setDenials] = useState([])
  const [appeals, setAppeals] = useState([])
  const [facilities, setFacilities] = useState([])
  const [contacts, setContacts] = useState([])

  useEffect(() => {
    const load = async () => {
      const [invoiceData, claimData, denialData, appealData, facilityData] = await Promise.all([
        apiFetch('/api/billing/invoices'),
        apiFetch('/api/billing/claims'),
        apiFetch('/api/billing/denials'),
        apiFetch('/api/billing/appeals'),
        apiFetch('/api/billing/facilities'),
      ])
      setInvoices(Array.isArray(invoiceData) ? invoiceData : [])
      setClaims(Array.isArray(claimData) ? claimData : [])
      setDenials(Array.isArray(denialData) ? denialData : [])
      setAppeals(Array.isArray(appealData) ? appealData : [])
      setFacilities(Array.isArray(facilityData) ? facilityData : [])
      if (Array.isArray(facilityData) && facilityData.length > 0) {
        const contactData = await apiFetch(`/api/billing/facilities/${facilityData[0].id}/contacts`)
        setContacts(Array.isArray(contactData) ? contactData : [])
      } else {
        setContacts([])
      }
    }
    load()
  }, [])

  const reportMetrics = useMemo(() => {
    const openInvoices = invoices.filter((invoice) => invoice.status !== 'PAID').length
    const totalAr = invoices.reduce((sum, invoice) => sum + (invoice.amount_due || 0), 0)
    return { openInvoices, totalAr, denials: denials.length }
  }, [invoices, denials])

  return (
    <div className="page">
      <SectionHeader eyebrow="Founder Billing" title="Revenue Command Center" />
      <div className="section-grid">
        <BillingSpine invoices={invoices} />
        <BillingReports metrics={reportMetrics} />
      </div>
      <div className="section-grid">
        <ClaimLifecycle claims={claims} />
      </div>
      <DenialAppealEngine denials={denials} appeals={appeals} />
      <FacilityContactSpine facilities={facilities} contacts={contacts} />
    </div>
  )
}
