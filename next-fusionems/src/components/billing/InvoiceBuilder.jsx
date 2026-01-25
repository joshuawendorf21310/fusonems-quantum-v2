import SectionHeader from '../SectionHeader.jsx'
import DataTable from '../DataTable.jsx'

export default function InvoiceBuilder({ items, subtotal }) {
  const columns = [
    { key: 'description', label: 'Description' },
    { key: 'code', label: 'Code' },
    { key: 'quantity', label: 'Qty' },
    { key: 'unit_price', label: 'Unit Price', render: (row) => `$${(row.unit_price / 100).toFixed(2)}` },
    { key: 'amount', label: 'Amount', render: (row) => `$${(row.amount / 100).toFixed(2)}` },
  ]

  return (
    <div className="panel">
      <SectionHeader eyebrow="Invoice Builder" title="Line Item Review" />
      <DataTable columns={columns} rows={items} emptyState="No line items added." />
      <div className="list-row" style={{ justifyContent: 'space-between', marginTop: '1rem' }}>
        <span className="list-title">Subtotal</span>
        <span className="list-sub">${(subtotal / 100).toFixed(2)}</span>
      </div>
    </div>
  )
}
