export default function DataTable({ columns, rows, emptyText = "Нет данных.", className = "" }) {
  return (
    <div className={`table-wrap ${className}`.trim()}>
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row, index) => (
              <tr key={row.id || row.trip_id || index}>
                {columns.map((column) => (
                  <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length}>
                <p className="empty-state">{emptyText}</p>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
