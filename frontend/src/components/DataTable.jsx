export default function DataTable({ columns, rows, emptyState }) {
  const template = `repeat(${columns.length}, minmax(0, 1fr))`

  return (
    <div className="table">
      <div className="table-header" style={{ gridTemplateColumns: template }}>
        {columns.map((column) => (
          <span key={column.key}>{column.label}</span>
        ))}
      </div>
      <div className="table-body">
        {rows.length === 0 ? (
          <div className="table-empty">{emptyState}</div>
        ) : (
          rows.map((row, index) => {
            const rowKey =
              row.id ||
              row.key ||
              row.unit_identifier ||
              row.invoice_number ||
              row.incident_number ||
              `${index}`

            return (
            <div
              className="table-row"
              style={{ gridTemplateColumns: template }}
              key={rowKey}
            >
              {columns.map((column) => (
                <span key={column.key} className={column.align || ''}>
                  {column.render ? column.render(row) : row[column.key]}
                </span>
              ))}
            </div>
          )})
        )}
      </div>
    </div>
  )
}
