export default function Alert({ children, tone = "info" }) {
  if (!children) {
    return null;
  }
  return <div className={`alert alert-${tone}`}>{children}</div>;
}
