import { useState } from "react";
import { Link } from "react-router-dom";

import {
  useArchiveTripsXlsxMutation,
  useDownloadTripsXlsxMutation,
  useTripsQuery
} from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import DataTable from "../components/ui/DataTable.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { saveDownload } from "../utils/downloads.js";
import {
  TRIP_STATUS_OPTIONS,
  formatDateTime,
  formatDistance,
  formatDuration,
  formatMoney,
  tripStatusLabel,
  transportLabel
} from "../utils/formatters.js";

const statusTone = {
  planned: "info",
  in_progress: "success",
  delivered: "neutral",
  cancelled: "danger"
};

export default function TripsListPage() {
  const [filters, setFilters] = useState({ status: "", date_from: "", date_to: "" });
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { data: trips = [], isError, isLoading } = useTripsQuery(filters);
  const [downloadTripsXlsx, { isLoading: isDownloading }] = useDownloadTripsXlsxMutation();
  const [archiveTripsXlsx, { isLoading: isArchiving }] = useArchiveTripsXlsxMutation();

  const updateFilter = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const handleDownload = async () => {
    setMessage("");
    setErrorMessage("");
    try {
      saveDownload(await downloadTripsXlsx(filters).unwrap());
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось скачать экспорт рейсов.");
    }
  };

  const handleArchive = async () => {
    setMessage("");
    setErrorMessage("");
    try {
      await archiveTripsXlsx(filters).unwrap();
      setMessage("Экспорт рейсов сохранен в архив.");
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось сохранить экспорт в архив.");
    }
  };

  const columns = [
    { key: "id", label: "№", render: (trip) => <Link to={`/trips/${trip.id}`}>#{trip.id}</Link> },
    { key: "cargo", label: "Груз", render: (trip) => trip.order?.cargo_name || "—" },
    { key: "transport", label: "Транспорт", render: (trip) => transportLabel(trip.transport) },
    {
      key: "status",
      label: "Статус",
      render: (trip) => (
        <Badge tone={statusTone[trip.status] || "neutral"}>{tripStatusLabel(trip.status)}</Badge>
      )
    },
    {
      key: "planned_start",
      label: "Плановый старт",
      render: (trip) => formatDateTime(trip.planned_start)
    },
    {
      key: "distance",
      label: "Расстояние",
      render: (trip) => formatDistance(trip.route_option?.distance_km)
    },
    {
      key: "cost",
      label: "Стоимость",
      render: (trip) => formatMoney(trip.route_option?.cost_rub)
    },
    {
      key: "duration",
      label: "Время",
      render: (trip) => formatDuration(trip.route_option?.duration_minutes)
    },
    {
      key: "actions",
      label: "Действие",
      render: (trip) => (
        <Link className="table-action" to={`/trips/${trip.id}`}>
          Открыть
        </Link>
      )
    }
  ];

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <PageShell eyebrow="Рейсы" title="Рейсы менеджера">
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}
      {isError ? <Alert tone="danger">Не удалось загрузить рейсы.</Alert> : null}
      <Card>
        <div className="toolbar toolbar-wrap">
          <label className="compact-field">
            Статус
            <select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
              {TRIP_STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="compact-field">
            Дата с
            <input
              type="date"
              value={filters.date_from}
              onChange={(event) => updateFilter("date_from", event.target.value)}
            />
          </label>
          <label className="compact-field">
            Дата по
            <input
              type="date"
              value={filters.date_to}
              onChange={(event) => updateFilter("date_to", event.target.value)}
            />
          </label>
          <div className="toolbar-actions">
            <Button variant="secondary" disabled={isDownloading} onClick={handleDownload}>
              {isDownloading ? "Готовим файл..." : "Скачать Excel"}
            </Button>
            <Button variant="secondary" disabled={isArchiving} onClick={handleArchive}>
              {isArchiving ? "Сохраняем..." : "В архив"}
            </Button>
          </div>
        </div>
        <DataTable columns={columns} rows={trips} emptyText="Рейсов по выбранным условиям нет." />
      </Card>
    </PageShell>
  );
}
