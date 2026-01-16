import { useAppData } from '../context/useAppData.js'
import SectionHeader from '../components/SectionHeader.jsx'
import DataTable from '../components/DataTable.jsx'
import StatusBadge from '../components/StatusBadge.jsx'
import {
  fallbackAcks,
  fallbackAppeals,
  fallbackClaimStatus,
  fallbackClaimSubmissions,
  fallbackEligibility,
  fallbackPayments,
  fallbackRemittances,
  fallbackStatements,
} from '../data/fallback.js'

export default function Billing() {
  const { invoices } = useAppData()
  const claims = fallbackClaimSubmissions
  const remittances = fallbackRemittances
  const acks = fallbackAcks
  const eligibility = fallbackEligibility
  const claimStatus = fallbackClaimStatus
  const statements = fallbackStatements
  const payments = fallbackPayments
  const appeals = fallbackAppeals

  const columns = [
    { key: 'invoice_number', label: 'Invoice' },
    { key: 'patient_name', label: 'Patient' },
    { key: 'payer', label: 'Payer' },
    {
      key: 'amount_due',
      label: 'Amount',
      render: (row) => `$${row.amount_due.toLocaleString()}`,
    },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const claimColumns = [
    { key: 'invoice_number', label: 'Invoice' },
    { key: 'clearinghouse', label: 'Clearinghouse' },
    { key: 'edi_version', label: 'EDI' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const remittanceColumns = [
    { key: 'payer', label: 'Payer' },
    { key: 'claim_reference', label: 'Claim Ref' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const ackColumns = [
    { key: 'ack_type', label: 'ACK' },
    { key: 'reference', label: 'Reference' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const eligibilityColumns = [
    { key: 'patient_name', label: 'Patient' },
    { key: 'payer', label: 'Payer' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const claimStatusColumns = [
    { key: 'claim_reference', label: 'Claim Ref' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const statementColumns = [
    { key: 'patient_name', label: 'Patient' },
    { key: 'balance_due', label: 'Balance' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const paymentColumns = [
    { key: 'source', label: 'Source' },
    { key: 'amount', label: 'Amount' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  const appealColumns = [
    { key: 'claim_reference', label: 'Claim Ref' },
    { key: 'status', label: 'Status', render: (row) => <StatusBadge value={row.status} /> },
  ]

  return (
    <div className="page">
      <SectionHeader
        eyebrow="Billing & Business Ops"
        title="Claims, Reconciliation, and Revenue"
        action={<button className="ghost-button">Submit to Office Ally</button>}
      />

      <div className="section-grid">
        <div className="panel">
          <DataTable columns={columns} rows={invoices} emptyState="No invoices generated." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="KPIs" title="Revenue Health" />
          <div className="stack">
            <div className="list-row">
              <div>
                <p className="list-title">Average AR Days</p>
                <p className="list-sub">24 days, improving</p>
              </div>
              <StatusBadge value="Dispatched" />
            </div>
            <div className="list-row">
              <div>
                <p className="list-title">Denied Claims</p>
                <p className="list-sub">3 in review, auto-correct suggestions ready</p>
              </div>
              <StatusBadge value="High" />
            </div>
          </div>
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="EDI" title="837P Submissions" />
          <DataTable columns={claimColumns} rows={claims} emptyState="No claim submissions." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Remittance" title="835 Imports" />
          <DataTable columns={remittanceColumns} rows={remittances} emptyState="No remittances." />
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="ACKs" title="999/277CA" />
          <DataTable columns={ackColumns} rows={acks} emptyState="No acknowledgments." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Eligibility" title="270/271 Checks" />
          <DataTable columns={eligibilityColumns} rows={eligibility} emptyState="No eligibility checks." />
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Claim Status" title="276/277 Responses" />
          <DataTable columns={claimStatusColumns} rows={claimStatus} emptyState="No status inquiries." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Patient Statements" title="Balance Notifications" />
          <DataTable columns={statementColumns} rows={statements} emptyState="No statements." />
        </div>
      </div>

      <div className="section-grid">
        <div className="panel">
          <SectionHeader eyebrow="Payments" title="Payment Posting" />
          <DataTable columns={paymentColumns} rows={payments} emptyState="No payments." />
        </div>
        <div className="panel">
          <SectionHeader eyebrow="Appeals" title="Appeal Packets" />
          <DataTable columns={appealColumns} rows={appeals} emptyState="No appeals yet." />
        </div>
      </div>
    </div>
  )
}
