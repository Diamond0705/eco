import { Link } from "react-router-dom";

import { useManagerDashboardQuery } from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { formatDistance, formatNumber } from "../utils/formatters.js";

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
      eyebrow="Панель менеджера"
      title="Ключевые показатели"
      actions={<Button to="/orders/create">Создать заявку</Button>}
    >
      <section className="dashboard-grid">
        <Card className="metric-card">
          <span className="metric-label">Мои заявки</span>
          <strong>{orders.total ?? 0}</strong>
          <p>
            Новые: {orders.by_status?.new ?? 0} · Рассчитанные:{" "}
            {orders.by_status?.calculated ?? 0}
          </p>
          <Link to="/orders">Открыть заявки</Link>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">Активные рейсы</span>
          <strong>{trips.active ?? 0}</strong>
          <p>
            План: {trips.planned ?? 0} · В пути: {trips.in_progress ?? 0}
          </p>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">Доставленные рейсы</span>
          <strong>{trips.delivered ?? 0}</strong>
          <p>
            {formatDistance(delivered.distance_km)} ·{" "}
            {formatNumber(delivered.fuel_liters, { maximumFractionDigits: 2 })} л топлива
          </p>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">CO2 доставленных</span>
          <strong>{formatNumber(delivered.co2_kg, { maximumFractionDigits: 2 })} кг</strong>
          <p>Средний эко-рейтинг: {delivered.average_eco_rating ?? "—"}</p>
        </Card>
      </section>

      <section className="feature-grid">
        <Card className="feature-card">
          <h2>Маршруты</h2>
          <p>
            Расчет и сравнение маршрутов будут перенесены в следующей фазе. Сейчас можно создать
            заявку и перейти к ее деталям.
          </p>
          <Button to="/orders" variant="secondary">
            Перейти к заявкам
          </Button>
        </Card>
        <Card className="feature-card">
          <h2>Отчеты</h2>
          <p>
            API для отчетов уже готов, React-страницы отчетов будут добавлены после основных
            операций с заявками и маршрутами.
          </p>
        </Card>
      </section>
    </PageShell>
  );
}
