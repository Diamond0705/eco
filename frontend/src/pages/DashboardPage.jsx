import { useSelector } from "react-redux";

import { selectCurrentUser } from "../features/auth/authSlice.js";

export default function DashboardPage() {
  const user = useSelector(selectCurrentUser);

  return (
    <main className="dashboard-page">
      <section className="summary-grid">
        <article className="summary-card primary-card">
          <p className="eyebrow">Phase 25</p>
          <h2>Каркас React SPA готов</h2>
          <p>
            Это базовая защищенная панель. Полные страницы заявок, маршрутов, рейсов и отчетов
            будут перенесены в следующих фазах.
          </p>
        </article>
        <article className="summary-card">
          <span className="metric-label">Пользователь</span>
          <strong>{user?.full_name || user?.username}</strong>
          <p>{user?.role === "admin" ? "Администратор" : "Менеджер"}</p>
        </article>
        <article className="summary-card">
          <span className="metric-label">API</span>
          <strong>JWT + DRF</strong>
          <p>Запросы идут через Vite proxy на `/api/` без CORS.</p>
        </article>
      </section>

      <section className="work-panel">
        <h2>Следующие разделы</h2>
        <div className="section-list">
          <span>Заявки</span>
          <span>Расчет маршрутов</span>
          <span>Карта Leaflet</span>
          <span>Рейсы</span>
          <span>Отчеты</span>
        </div>
      </section>
    </main>
  );
}
