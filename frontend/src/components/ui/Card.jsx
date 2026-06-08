export default function Card({ children, className = "", variant = "default" }) {
  return <section className={`card card-${variant} ${className}`.trim()}>{children}</section>;
}
