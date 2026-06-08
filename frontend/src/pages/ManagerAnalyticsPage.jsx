import { Link } from "react-router-dom";

import { useManagerDashboardQuery } from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Card from "../components/ui/Card.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { formatDistance, formatNumber } from "../utils/formatters.js";

export default function ManagerAnalyticsPage() {
  const { data, isError, isLoading } = useManagerDashboardQuery();

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError) {
    return <Alert tone="danger">Не удалось загрузить аналитику.</Alert>;
  }

  const orders = data?.orders || {};
  const trips = data?.trips || {};
  const delivered = data?.delivered || {};

  return (
    <PageShell
      title="Аналитика"
      subtitle="Сводные показатели по вашим заявкам, рейсам, топливу и выбросам."
      variant="wide"
    >
      <section className="report-summary-grid">
        <Card className="metric-card">
          <span className="metric-label">Заявки</span>
          <strong>{formatNumber(orders.total, { maximumFractionDigits: 0 })}</strong>
          <p>
            Новые: {orders.by_status?.new ?? 0} · Рассчитанные:{" "}
            {orders.by_status?.calculated ?? 0}
          </p>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">Рейсы</span>
          <strong>{formatNumber(trips.delivered, { maximumFractionDigits: 0 })}</strong>
          <p>
            Активные: {trips.active ?? 0} · В пути: {trips.in_progress ?? 0}
          </p>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">Расстояние</span>
          <strong>{formatDistance(delivered.distance_km)}</strong>
          <p>{formatNumber(delivered.fuel_liters, { maximumFractionDigits: 2 })} л топлива</p>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">CO2</span>
          <strong>{formatNumber(delivered.co2_kg, { maximumFractionDigits: 2 })} кг</strong>
          <p>Средний эко-рейтинг: {delivered.average_eco_rating ?? "—"}</p>
        </Card>
      </section>

      <Card className="actions-card">
        <h2>Детализация</h2>
        <p>
          Подробные выбросы по доставленным рейсам доступны в отчете. Там можно выбрать период,
          скачать PDF или Excel и сохранить документ в архив.
        </p>
        <div className="form-actions">
          <Link className="button" to="/reports/emissions">
            Открыть отчет
          </Link>
          <Link className="button button-secondary" to="/archive">
            Архив документов
          </Link>
        </div>
      </Card>
    </PageShell>
  );
}
