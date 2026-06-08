import { Link } from "react-router-dom";

export default function Button({
  children,
  to,
  variant = "primary",
  type = "button",
  disabled = false,
  onClick
}) {
  const className = `button button-${variant}`;

  if (to) {
    return (
      <Link className={className} to={to}>
        {children}
      </Link>
    );
  }

  return (
    <button className={className} type={type} disabled={disabled} onClick={onClick}>
      {children}
    </button>
  );
}
