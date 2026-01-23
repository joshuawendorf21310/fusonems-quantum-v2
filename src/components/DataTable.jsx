import PropTypes from "prop-types"
import clsx from "clsx"

export default function DataTable({
  columns,
  rows = [],
  emptyState = "No records found.",
  getRowKey,
}) {
  const safeColumns = Array.isArray(columns) ? columns : []
  const safeRows = Array.isArray(rows) ? rows : []

  const colCount = Math.max(safeColumns.length, 1)
  const template = `repeat(${colCount}, minmax(0, 1fr))`
  const isEmpty = safeRows.length === 0

  return (
    <section
      className="table"
      role="table"
      aria-rowcount={safeRows.length}
      aria-colcount={colCount}
    >
      <span className="sr-only">
        Data table with {safeRows.length} rows and {colCount} columns
      </span>
      <header
        className="table-header"
        role="row"
        style={{ gridTemplateColumns: template }}
      >
        {safeColumns.map((column) => (
          <span
            key={column.key}
            role="columnheader"
            scope="col"
            className={clsx("table-header-cell", column.align)}
            aria-sort="none"
          >
            {column.label}
          </span>
        ))}
      </header>

      <div className="table-body" role="rowgroup">
        {isEmpty ? (
          <div className="table-empty" role="note">
            {emptyState}
          </div>
        ) : (
          safeRows.map((row, index) => {
            const rowKey =
              (getRowKey && getRowKey(row)) ||
              row.id ||
              row.key ||
              row.unit_identifier ||
              row.invoice_number ||
              row.incident_number ||
              String(index)

            return (
              <div
                className="table-row"
                role="row"
                style={{ gridTemplateColumns: template }}
                key={rowKey}
              >
                {safeColumns.map((column) => (
                  <span
                    key={column.key}
                    role="cell"
                    className={clsx("table-cell", column.align)}
                  >
                    {column.render
                      ? column.render(row)
                      : row?.[column.key] ?? ""}
                  </span>
                ))}
              </div>
            )
          })
        )}
      </div>
    </section>
  )
}

DataTable.propTypes = {
  columns: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      align: PropTypes.string,
      render: PropTypes.func,
    })
  ).isRequired,
  rows: PropTypes.array,
  emptyState: PropTypes.string,
  getRowKey: PropTypes.func,
}
