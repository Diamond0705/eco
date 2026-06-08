import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useSelector } from "react-redux";

import { useLogoutMutation } from "../api/authApi.js";
import { selectCurrentUser } from "../features/auth/authSlice.js";

export default function AppLayout() {
  const navigate = useNavigate();
  const user = useSelector(selectCurrentUser);
  const [logout] = useLogoutMutation();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <NavLink to="/dashboard" className="brand" aria-label="EcoLogist">
          <img src="/static/img/ecologist-truck-mark.png" alt="" />
          <span>EcoLogist</span>
        </NavLink>
        <nav className="main-nav" aria-label="Основная навигация">
          <NavLink to="/dashboard">Панель</NavLink>
          <span className="nav-placeholder">Заявки</span>
          <span className="nav-placeholder">Маршруты</span>
          <span className="nav-placeholder">Рейсы</span>
          <span className="nav-placeholder">Отчеты</span>
        </nav>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Одностраничное приложение</p>
            <h1>Рабочее место EcoLogist</h1>
          </div>
          <div className="user-menu">
            <span>{user?.full_name || user?.username}</span>
            <span className="role-pill">{user?.role === "admin" ? "Администратор" : "Менеджер"}</span>
            <button type="button" onClick={handleLogout}>
              Выйти
            </button>
          </div>
        </header>
        <Outlet />
      </div>
    </div>
  );
}
