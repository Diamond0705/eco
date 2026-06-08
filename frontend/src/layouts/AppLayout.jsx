import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";

import { useLogoutMutation } from "../api/authApi.js";
import { selectCurrentUser } from "../features/auth/authSlice.js";

const managerLinks = [
  { to: "/dashboard", label: "Панель" },
  { to: "/orders", label: "Заявки" },
  { to: "/orders/create", label: "Создать заявку" },
  { to: "/trips", label: "Рейсы" },
  { to: "/analytics", label: "Аналитика" },
  { to: "/reports/emissions", label: "Отчеты" },
  { to: "/archive", label: "Архив" },
  { to: "/profile", label: "Профиль" }
];

export default function AppLayout() {
  const navigate = useNavigate();
  const user = useSelector(selectCurrentUser);
  const [logout] = useLogoutMutation();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="manager-spa-shell">
      <header className="manager-topbar">
        <NavLink to="/dashboard" className="manager-brand" aria-label="EcoLogist">
          <img src="/static/img/ecologist-truck-mark.png" alt="" />
          <span>
            <strong>EcoLogist</strong>
            <small>Система планирования грузоперевозок</small>
          </span>
        </NavLink>
        <nav
          className="manager-nav"
          aria-label={`Основная навигация менеджера ${user?.username || ""}`}
        >
          {managerLinks.map((link) => (
            <NavLink key={link.to} to={link.to}>
              {link.label}
            </NavLink>
          ))}
          <button type="button" className="manager-nav-button" onClick={handleLogout}>
            Выйти
          </button>
        </nav>
      </header>
      <div className="workspace manager-workspace">
        <Outlet />
      </div>
    </div>
  );
}
