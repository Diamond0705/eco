import { useState } from "react";
import { Link } from "react-router-dom";

import {
  useArchiveTripsXlsxMutation,
  useDownloadTripsXlsxMutation,
  useTripsQuery
} from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
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
  tripStatusLabel
} from "../utils/formatters.js";

export default function TripsListPage() {
  const [filters, setFilters] = useState({ status: "" });
  const [selectedStatus, setSelectedStatus] = useState("");
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { data: trips = [], isError, isLoading } = useTripsQuery(filters);
  const [downloadTripsXlsx, { isLoading: isDownloading }] = useDownloadTripsXlsxMutation();
  const [archiveTripsXlsx, { isLoading: isArchiving }] = useArchiveTripsXlsxMutation();

  const applyFilters = (event) => {
    event.preventDefault();
    setFilters({ status: selectedStatus });
  };

  const resetFilters = () => {
    setSelectedStatus("");
    setFilters({ status: "" });
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
    { key: "id", label: "Рейс", render: (trip) => `№${trip.id}` },
    { key: "order", label: "Заявка", render: (trip) => (trip.order?.id ? `№${trip.order.id}` : "—") },
    { key: "cargo", label: "Груз", render: (trip) => trip.order?.cargo_name || "—" },
    { key: "route", label: "Маршрут", render: (trip) => trip.display_route_name || trip.route_option?.name || "—" },
    {
      key: "status",
      label: "Статус",
      render: (trip) => tripStatusLabel(trip.status)
    },
    {
      key: "distance",
      label: "Расстояние",
      render: (trip) => formatDistance(trip.route_option?.distance_km)
    },
    {
      key: "actual_start",
      label: "Факт. начало",
      render: (trip) => formatDateTime(trip.actual_start)
    },
    {
      key: "actual_finish",
      label: "Факт. завершение",
      render: (trip) => formatDateTime(trip.actual_finish)
    },
    {
      key: "actions",
      label: "",
      render: (trip) => (
        <Link className="button button-primary table-action-button" to={`/trips/${trip.id}`}>
          Открыть
        </Link>
      )
    }
  ];

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <PageShell
      title="Рейсы"
      subtitle="Список рейсов по утвержденным маршрутам"
      className="trips-list-panel"
      variant="wide"
      actions={
        <>
          <Button variant="secondary" disabled={isDownloading} onClick={handleDownload}>
            {isDownloading ? "Готовим файл..." : "Экспорт Excel"}
          </Button>
          <Button variant="secondary" disabled={isArchiving} onClick={handleArchive}>
            {isArchiving ? "Сохраняем..." : "Сохранить Excel в архив"}
          </Button>
          <Button to="/orders" variant="secondary">
            К заявкам
          </Button>
        </>
      }
    >
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}
      {isError ? <Alert tone="danger">Не удалось загрузить рейсы.</Alert> : null}
      <Card className="trips-list-card">
        <form className="trips-filter-form" onSubmit={applyFilters}>
          <label htmlFor="trip-status">Статус</label>
          <select
            id="trip-status"
            value={selectedStatus}
            onChange={(event) => setSelectedStatus(event.target.value)}
          >
            {TRIP_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <Button type="submit" variant="secondary">
            Показать
          </Button>
          <Button type="button" variant="secondary" onClick={resetFilters}>
            Сбросить
          </Button>
        </form>
        <DataTable
          columns={columns}
          rows={trips}
          emptyText="Рейсы по выбранным фильтрам не найдены."
          className="trips-table-wrap"
        />
      </Card>
    </PageShell>
  );
}
