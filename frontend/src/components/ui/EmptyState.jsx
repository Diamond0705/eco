export default function EmptyState({ title = "Нет данных", children }) {
  return (
    <div className="empty-panel">
      <h2>{title}</h2>
      {children ? <p>{children}</p> : null}
    </div>
  );
}
