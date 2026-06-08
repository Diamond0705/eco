export default function PageShell({
  eyebrow,
  title,
  subtitle,
  actions,
  children,
  className = "",
  variant = "default"
}) {
  const classes = ["page-shell", `page-shell-${variant}`, className].filter(Boolean).join(" ");

  return (
    <main className={classes}>
      <div className="page-heading">
        <div>
          {eyebrow ? <p className="eyebrow">{eyebrow}</p> : null}
          <h1>{title}</h1>
          {subtitle ? <p className="muted">{subtitle}</p> : null}
        </div>
        {actions ? <div className="page-actions">{actions}</div> : null}
      </div>
      {children}
    </main>
  );
}
