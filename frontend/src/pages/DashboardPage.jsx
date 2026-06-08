import { Link } from "react-router-dom";

import { useManagerDashboardQuery } from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { formatDistance, formatNumber } from "../utils/formatters.js";

function Icon({ children, className = "" }) {
  return (
    <span className={`manager-card-icon ${className}`.trim()} aria-hidden="true">
      <svg viewBox="0 0 24 24" focusable="false">
        {children}
      </svg>
    </span>
  );
}

function LeafIcon() {
  return (
    <svg viewBox="0 0 24 24" focusable="false">
      <path d="M20 4c-7 0-12 4-12 10 0 4 3 6 6 6 5 0 8-5 8-14V4z" />
      <path d="M14 14c-3 1-5 3-6 6" />
    </svg>
  );
}

export default function DashboardPage() {
  const { data, isError, isLoading } = useManagerDashboardQuery();

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError) {
    return <Alert tone="danger">Не удалось загрузить данные панели.</Alert>;
  }

  const orders = data?.orders || {};
  const trips = data?.trips || {};
  const delivered = data?.delivered || {};

  return (
    <PageShell
      className="manager-dashboard-panel"
      title="Панель менеджера"
      subtitle="Ключевые показатели по вашим заявкам, рейсам и выбросам"
      variant="wide"
    >
      <section className="manager-metrics-grid">
        <Card className="manager-metric-card">
          <Icon>
            <path d="M7 3h7l4 4v14H7z" />
            <path d="M14 3v5h5" />
            <path d="M10 12h5" />
            <path d="M10 16h5" />
          </Icon>
          <h2>Мои заявки</h2>
          <p className="stat-value">{orders.total ?? 0}</p>
          <p className="metric-note">
            Новые: {orders.by_status?.new ?? 0} · Рассчитанные:{" "}
            {orders.by_status?.calculated ?? 0}
          </p>
          <div className="manager-card-actions">
            <Link className="manager-action-button" to="/orders">
              Заявки <span aria-hidden="true">→</span>
            </Link>
            <Link className="manager-action-button manager-action-button-wide" to="/orders/create">
              Создать заявку <span aria-hidden="true">→</span>
            </Link>
          </div>
        </Card>
        <Card className="manager-metric-card">
          <Icon>
            <path d="M3 6h11v10H3z" />
            <path d="M14 10h4l3 3v3h-7z" />
            <circle cx="7" cy="18" r="2" />
            <circle cx="18" cy="18" r="2" />
          </Icon>
          <h2>Активные рейсы</h2>
          <p className="stat-value">{trips.active ?? 0}</p>
          <p className="metric-note">
            План: {trips.planned ?? 0} · В пути: {trips.in_progress ?? 0}
          </p>
          <div className="manager-card-actions">
            <Link className="manager-action-button" to="/trips">
              Рейсы <span aria-hidden="true">→</span>
            </Link>
          </div>
        </Card>
        <Card className="manager-metric-card">
          <Icon>
            <rect x="5" y="4" width="14" height="16" rx="2" />
            <path d="m9 12 2 2 4-5" />
          </Icon>
          <h2>Доставленные рейсы</h2>
          <p className="stat-value">{trips.delivered ?? 0}</p>
          <p className="metric-note">
            {formatDistance(delivered.distance_km)} ·{" "}
            {formatNumber(delivered.fuel_liters, { maximumFractionDigits: 2 })} л топлива
          </p>
          <div className="manager-card-actions">
            <Link className="manager-action-button manager-action-button-wide" to="/reports/emissions">
              Отчет по выбросам <span aria-hidden="true">→</span>
            </Link>
          </div>
        </Card>
        <Card className="manager-metric-card">
          <Icon>
            <path d="M20 4c-7 0-12 4-12 10 0 4 3 6 6 6 5 0 8-5 8-14V4z" />
            <path d="M14 14c-3 1-5 3-6 6" />
          </Icon>
          <h2>CO2 доставленных</h2>
          <p className="stat-value">
            {formatNumber(delivered.co2_kg, { maximumFractionDigits: 2 })} кг
          </p>
          <p className="metric-note">Средний эко-рейтинг: {delivered.average_eco_rating ?? "—"}</p>
          <div className="manager-card-actions">
            <Link className="manager-action-button" to="/reports/emissions">
              Аналитика <span aria-hidden="true">→</span>
            </Link>
          </div>
        </Card>
      </section>

      <section className="manager-feature-grid">
        <Card className="manager-feature-card manager-feature-card-map">
          <Icon className="manager-feature-icon">
            <path d="m9 18-6 3V6l6-3 6 3 6-3v15l-6 3z" />
            <path d="M9 3v15" />
            <path d="M15 6v15" />
          </Icon>
          <h2>Маршруты</h2>
          <p>
            Сравнивайте рассчитанные варианты маршрутов по стоимости, выбросам и эко-рейтингу.
          </p>
          <img
            className="manager-map-illustration"
            src="/static/img/manager-map-illustration.png"
            alt=""
          />
          <div className="manager-card-actions">
            <Button to="/orders" variant="secondary" className="manager-action-button manager-action-button-wide">
              Открыть карту <span aria-hidden="true">→</span>
            </Button>
          </div>
        </Card>
        <Card className="manager-feature-card manager-feature-card-report">
          <Icon className="manager-feature-icon">
            <path d="M5 20V10" />
            <path d="M12 20V4" />
            <path d="M19 20v-7" />
            <path d="M3 20h18" />
          </Icon>
          <h2>Отчеты</h2>
          <p>
            Смотрите суммарные выбросы по доставленным рейсам и скачивайте PDF.
          </p>
          <div className="manager-report-layout">
            <div className="manager-card-actions">
              <Button to="/reports/emissions" variant="secondary" className="manager-action-button">
                Отчеты <span aria-hidden="true">→</span>
              </Button>
            </div>
            <img
              className="manager-report-illustration"
              src="/static/img/manager-report-illustration.png"
              alt=""
            />
          </div>
        </Card>
      </section>
      <p className="manager-dashboard-footer">
        <span className="manager-footer-leaf" aria-hidden="true">
          <LeafIcon />
        </span>
        EcoLogist — умные логистические решения для зелёного будущего
        <span className="manager-footer-leaf" aria-hidden="true">
          <LeafIcon />
        </span>
      </p>
    </PageShell>
  );
}
