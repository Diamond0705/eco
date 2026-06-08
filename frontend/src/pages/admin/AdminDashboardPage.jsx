import { Link } from "react-router-dom";

import {
  useAdminDashboardQuery,
  useArchiveAdminDashboardXlsxMutation,
  useDownloadAdminDashboardXlsxMutation
} from "../../api/adminApi.js";
import Alert from "../../components/ui/Alert.jsx";
import Button from "../../components/ui/Button.jsx";
import Card from "../../components/ui/Card.jsx";
import LoadingState from "../../components/ui/LoadingState.jsx";
import { saveDownload } from "../../utils/downloads.js";
import { formatEmissions, formatMoney, formatNumber } from "../../utils/formatters.js";

function MetricCard({ icon, label, value, hint }) {
  return (
    <Card className="admin-metric-card">
      <span className="admin-metric-icon" aria-hidden="true">
        {icon}
      </span>
      <span className="metric-label">{label}</span>
      <strong>{value}</strong>
      <p>{hint}</p>
    </Card>
  );
}

function TopList({ title, rows, renderName }) {
  return (
    <Card className="admin-list-card">
      <h2>{title}</h2>
      <ol className="admin-top-list">
        {rows.length ? (
          rows.map((row, index) => (
            <li key={`${title}-${index}`}>
              <span>{index + 1}</span>
              <strong>{renderName(row)}</strong>
              <em>{formatNumber(row.delivered_count)} рейс.</em>
            </li>
          ))
        ) : (
          <li className="admin-empty-row">Пока нет доставленных рейсов.</li>
        )}
      </ol>
    </Card>
  );
}

export default function AdminDashboardPage() {
  const { data, isError, isLoading } = useAdminDashboardQuery();
  const [downloadXlsx, { isLoading: isDownloading }] = useDownloadAdminDashboardXlsxMutation();
  const [archiveXlsx, { isLoading: isArchiving, isSuccess: isArchived }] =
    useArchiveAdminDashboardXlsxMutation();

  const handleDownload = async () => {
    const download = await downloadXlsx().unwrap();
    saveDownload(download);
  };

  const handleArchive = async () => {
    await archiveXlsx().unwrap();
  };

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError) {
    return <Alert tone="danger">Не удалось загрузить панель администратора.</Alert>;
  }

  const users = data?.users || {};
  const transports = data?.transports || {};
  const orders = data?.orders || {};
  const trips = data?.trips || {};
  const company = data?.company || {};
  const topManagers = data?.top_managers || [];
  const topTransports = data?.top_transports || [];

  return (
    <section className="admin-page">
      <div className="admin-hero">
        <div>
          <h1>Панель администратора</h1>
          <p>Сводные показатели по пользователям, транспорту, заявкам и рейсам компании.</p>
        </div>
        <div className="admin-hero-actions">
          <Button onClick={handleDownload} disabled={isDownloading}>
            Скачать Excel
          </Button>
          <Button variant="secondary" onClick={handleArchive} disabled={isArchiving}>
            Сохранить Excel в архив
          </Button>
          <a className="button button-secondary" href="/admin/">
            Django Admin
          </a>
        </div>
      </div>

      {isArchived ? <Alert tone="success">Сводка сохранена в архив документов.</Alert> : null}

      <div className="admin-metrics-grid">
        <MetricCard
          icon="П"
          label="Пользователи"
          value={formatNumber(users.total)}
          hint={`Менеджеры: ${formatNumber(users.managers)}`}
        />
        <MetricCard
          icon="Т"
          label="Транспорт"
          value={formatNumber(transports.total)}
          hint="Количество добавленного транспорта."
        />
        <MetricCard
          icon="З"
          label="Заявки"
          value={formatNumber(orders.total)}
          hint="Все заявки компании."
        />
        <MetricCard
          icon="Р"
          label="Рейсы"
          value={formatNumber(trips.total)}
          hint={`Доставленные: ${formatNumber(trips.delivered)}`}
        />
        <MetricCard
          icon="CO2"
          label="Выбросы CO2"
          value={formatEmissions(company.co2_kg, "кг")}
          hint="По доставленным рейсам компании."
        />
        <MetricCard
          icon="₽"
          label="Стоимость"
          value={formatMoney(company.cost_rub)}
          hint="Суммарная стоимость по доставленным рейсам."
        />
        <MetricCard
          icon="Л"
          label="Суммарные выбросы"
          value={`${formatEmissions(company.co2_kg, "кг")} CO2`}
          hint={`NOx: ${formatEmissions(company.nox_g, "г")} · PM: ${formatEmissions(company.pm_g, "г")}`}
        />
        <MetricCard
          icon="★"
          label="Средний эко-рейтинг"
          value={formatNumber(company.average_eco_rating, { maximumFractionDigits: 2 })}
          hint="По доставленным рейсам компании."
        />
        <MetricCard
          icon="КМ"
          label="CO2 на км"
          value={company.average_co2_kg_per_km || "—"}
          hint="Среднее по сохраненным расчетным деталям."
        />
        <MetricCard
          icon="ТК"
          label="CO2 на тонно-км"
          value={company.average_co2_kg_per_ton_km || "—"}
          hint="Показатель доступен для рейсов с весом груза."
        />
      </div>

      <div className="admin-dashboard-lists">
        <TopList
          title="Топ менеджеров по завершенным рейсам"
          rows={topManagers}
          renderName={(row) =>
            `${row.order__manager__last_name || ""} ${row.order__manager__first_name || ""}`.trim() ||
            row.order__manager__username
          }
        />
        <TopList
          title="Топ транспорта по завершенным рейсам"
          rows={topTransports}
          renderName={(row) => `${row.order__transport__plate_number} — ${row.order__transport__model}`}
        />
      </div>

      <p className="admin-footnote">
        Документы, сохраненные в архив, доступны в разделе <Link to="/admin/archive">Архив</Link>.
      </p>
    </section>
  );
}
