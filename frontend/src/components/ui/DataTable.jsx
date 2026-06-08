export default function DataTable({ columns, rows, emptyText = "Нет данных.", className = "" }) {
  if (!rows.length) {
    return <p className="empty-state">{emptyText}</p>;
  }

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
          {rows.map((row, index) => (
            <tr key={row.id || row.trip_id || index}>
              {columns.map((column) => (
                <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
