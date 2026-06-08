import { useState } from "react";
import { Link } from "react-router-dom";

import {
  useArchiveEmissionsPdfMutation,
  useArchiveEmissionsXlsxMutation,
  useDownloadEmissionsPdfMutation,
  useDownloadEmissionsXlsxMutation,
  useEmissionsReportQuery
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
  formatDateTime,
  formatDistance,
  formatEmissions,
  formatFuel,
  formatMoney,
  formatNumber
} from "../utils/formatters.js";

export default function EmissionsReportPage() {
  const [filters, setFilters] = useState({ date_from: "", date_to: "" });
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { data: report, isError, isLoading } = useEmissionsReportQuery(filters);
  const [downloadPdf, { isLoading: isDownloadingPdf }] = useDownloadEmissionsPdfMutation();
  const [downloadXlsx, { isLoading: isDownloadingXlsx }] = useDownloadEmissionsXlsxMutation();
  const [archivePdf, { isLoading: isArchivingPdf }] = useArchiveEmissionsPdfMutation();
  const [archiveXlsx, { isLoading: isArchivingXlsx }] = useArchiveEmissionsXlsxMutation();

  const updateFilter = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const handleDownload = async (format) => {
    setMessage("");
    setErrorMessage("");
    try {
      const download =
        format === "pdf"
          ? await downloadPdf(filters).unwrap()
          : await downloadXlsx(filters).unwrap();
      saveDownload(download);
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось скачать отчет.");
    }
  };

  const handleArchive = async (format) => {
    setMessage("");
    setErrorMessage("");
    try {
      if (format === "pdf") {
        await archivePdf(filters).unwrap();
      } else {
        await archiveXlsx(filters).unwrap();
      }
      setMessage("Отчет сохранен в архив.");
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось сохранить отчет в архив.");
    }
  };

  if (isLoading) {
    return <LoadingState />;
  }

  const summary = report?.summary || {};
  const rows = report?.rows || [];

  const columns = [
    {
      key: "trip_id",
      label: "Рейс",
      render: (row) => <Link to={`/trips/${row.trip_id}`}>#{row.trip_id}</Link>
    },
    { key: "finish_date", label: "Дата", render: (row) => formatDateTime(row.finish_date) },
    { key: "cargo", label: "Груз" },
    { key: "transport", label: "Транспорт" },
    { key: "distance", label: "Км", render: (row) => formatDistance(row.distance_km) },
    { key: "fuel", label: "Топливо", render: (row) => formatFuel(row.fuel_liters) },
    { key: "cost", label: "Стоимость", render: (row) => formatMoney(row.cost_rub) },
    { key: "co2", label: "CO2", render: (row) => formatEmissions(row.co2_kg, "кг") },
    { key: "nox", label: "NOx", render: (row) => formatEmissions(row.nox_g, "г") },
    { key: "pm", label: "PM", render: (row) => formatEmissions(row.pm_g, "г") },
    {
      key: "rating",
      label: "Эко-рейтинг",
      render: (row) => formatNumber(row.eco_rating, { maximumFractionDigits: 2 })
    },
    {
      key: "tolls",
      label: "Платные",
      render: (row) => <Badge tone={row.has_tolls ? "info" : "neutral"}>{row.has_tolls ? "Есть" : "Нет"}</Badge>
    }
  ];

  return (
    <PageShell eyebrow="Отчеты" title="Отчет по выбросам">
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}
      {isError ? <Alert tone="danger">Не удалось загрузить отчет.</Alert> : null}
      {report?.filters?.error_message ? <Alert tone="danger">{report.filters.error_message}</Alert> : null}

      <Card>
        <div className="toolbar toolbar-wrap">
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
            <Button variant="secondary" disabled={isDownloadingPdf} onClick={() => handleDownload("pdf")}>
              {isDownloadingPdf ? "PDF..." : "Скачать PDF"}
            </Button>
            <Button variant="secondary" disabled={isDownloadingXlsx} onClick={() => handleDownload("xlsx")}>
              {isDownloadingXlsx ? "Excel..." : "Скачать Excel"}
            </Button>
            <Button variant="secondary" disabled={isArchivingPdf} onClick={() => handleArchive("pdf")}>
              {isArchivingPdf ? "Сохраняем..." : "PDF в архив"}
            </Button>
            <Button variant="secondary" disabled={isArchivingXlsx} onClick={() => handleArchive("xlsx")}>
              {isArchivingXlsx ? "Сохраняем..." : "Excel в архив"}
            </Button>
          </div>
        </div>
      </Card>

      <section className="report-summary-grid">
        <Card className="metric-card">
          <span className="metric-label">Рейсы</span>
          <strong>{formatNumber(summary.trips_count, { maximumFractionDigits: 0 })}</strong>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">Расстояние</span>
          <strong>{formatDistance(summary.distance_km)}</strong>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">Стоимость</span>
          <strong>{formatMoney(summary.cost_rub)}</strong>
        </Card>
        <Card className="metric-card">
          <span className="metric-label">CO2</span>
          <strong>{formatEmissions(summary.co2_kg, "кг")}</strong>
        </Card>
      </section>

      <Card>
        <DataTable columns={columns} rows={rows} emptyText="Доставленных рейсов за период нет." />
      </Card>
    </PageShell>
  );
}
