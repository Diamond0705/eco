import { Link, NavLink } from "react-router-dom";

export default function AuthLayout({ children, pageClassName = "" }) {
  return (
    <main className={`auth-page ${pageClassName}`}>
      <header className="auth-topbar">
        <nav className="auth-nav" aria-label="Основная навигация">
          <Link className="auth-brand" to="/login">
            <img
              className="auth-brand-mark"
              src="/static/img/ecologist-truck-mark.png"
              alt=""
            />
            <span className="auth-brand-text">
              <span className="auth-logo">EcoLogist</span>
              <span className="auth-subtitle">Система планирования грузоперевозок</span>
            </span>
          </Link>
          <div className="auth-links">
            <NavLink to="/login">Войти</NavLink>
            <NavLink to="/register">Регистрация</NavLink>
          </div>
        </nav>
      </header>
      <div className="auth-main">{children}</div>
    </main>
  );
}
