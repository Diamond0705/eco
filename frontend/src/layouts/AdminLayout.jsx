import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";

import { useLogoutMutation } from "../api/authApi.js";
import { selectCurrentUser } from "../features/auth/authSlice.js";

const adminLinks = [
  { to: "/admin/dashboard", label: "Панель" },
  { to: "/admin/archive", label: "Архив" },
  { to: "/admin/users", label: "Пользователи" },
  { to: "/admin/transports", label: "Транспорт" },
  { to: "/admin/locations", label: "Локации" },
  { to: "/admin/eco-standards", label: "Экостандарты" },
  { to: "/admin/calculation-settings", label: "Экорасчет" },
  { to: "/admin/profile", label: "Профиль" }
];

export default function AdminLayout() {
  const navigate = useNavigate();
  const user = useSelector(selectCurrentUser);
  const [logout] = useLogoutMutation();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="admin-spa-shell">
      <header className="admin-topbar">
        <NavLink to="/admin/dashboard" className="admin-brand" aria-label="EcoLogist">
          <img src="/static/img/ecologist-truck-mark.png" alt="" />
          <span>
            <strong>EcoLogist</strong>
            <small>Система планирования грузоперевозок</small>
          </span>
        </NavLink>
        <nav className="admin-nav" aria-label="Навигация администратора">
          {adminLinks.map((link) => (
            <NavLink key={link.to} to={link.to}>
              {link.label}
            </NavLink>
          ))}
          <button type="button" className="admin-nav-button" onClick={handleLogout}>
            Выйти
          </button>
        </nav>
      </header>
      <main className="admin-main" aria-label={`Администратор ${user?.username || ""}`}>
        <Outlet />
      </main>
    </div>
  );
}
