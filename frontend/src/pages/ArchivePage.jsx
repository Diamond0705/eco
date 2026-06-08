import { useState } from "react";
import { Link } from "react-router-dom";

import {
  useArchiveDocumentsQuery,
  useDeleteArchiveDocumentMutation,
  useDownloadArchiveDocumentMutation
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
  DOCUMENT_TYPE_OPTIONS,
  FILE_FORMAT_OPTIONS,
  documentTypeLabel,
  formatBytes,
  formatDate,
  formatDateTime
} from "../utils/formatters.js";

export default function ArchivePage() {
  const [filters, setFilters] = useState({
    document_type: "",
    file_format: "",
    date_from: "",
    date_to: "",
    q: ""
  });
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { data: documents = [], isError, isLoading } = useArchiveDocumentsQuery(filters);
  const [downloadDocument, { isLoading: isDownloading }] = useDownloadArchiveDocumentMutation();
  const [deleteDocument, { isLoading: isDeleting }] = useDeleteArchiveDocumentMutation();

  const updateFilter = (key, value) => {
    setFilters((current) => ({ ...current, [key]: value }));
  };

  const handleDownload = async (document) => {
    setMessage("");
    setErrorMessage("");
    try {
      saveDownload(await downloadDocument(document.id).unwrap());
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось скачать документ.");
    }
  };

  const handleDelete = async (document) => {
    if (!window.confirm(`Удалить документ «${document.title}» из архива?`)) {
      return;
    }
    setMessage("");
    setErrorMessage("");
    try {
      await deleteDocument(document.id).unwrap();
      setMessage("Документ удален из архива.");
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось удалить документ.");
    }
  };

  const columns = [
    {
      key: "title",
      label: "Документ",
      render: (document) => (
        <div className="document-title-cell">
          <strong>{document.title}</strong>
          <span>{documentTypeLabel(document.document_type, document.document_type_display)}</span>
        </div>
      )
    },
    {
      key: "format",
      label: "Формат",
      render: (document) => <Badge tone="neutral">{document.file_format_display || document.file_format}</Badge>
    },
    { key: "size", label: "Размер", render: (document) => formatBytes(document.file_size_bytes) },
    { key: "created", label: "Создан", render: (document) => formatDateTime(document.created_at) },
    {
      key: "period",
      label: "Период",
      render: (document) =>
        document.date_from || document.date_to
          ? `${formatDate(document.date_from)} — ${formatDate(document.date_to)}`
          : "—"
    },
    {
      key: "related",
      label: "Связь",
      render: (document) => {
        if (document.related_trip_id) {
          return <Link to={`/trips/${document.related_trip_id}`}>Рейс #{document.related_trip_id}</Link>;
        }
        if (document.related_order_id) {
          return <Link to={`/orders/${document.related_order_id}`}>Заявка #{document.related_order_id}</Link>;
        }
        return "—";
      }
    },
    {
      key: "actions",
      label: "Действия",
      render: (document) => (
        <div className="table-actions">
          <button
            className="table-button"
            type="button"
            disabled={isDownloading}
            onClick={() => handleDownload(document)}
          >
            Скачать
          </button>
          <button
            className="table-button table-button-danger"
            type="button"
            disabled={isDeleting}
            onClick={() => handleDelete(document)}
          >
            Удалить
          </button>
        </div>
      )
    }
  ];

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <PageShell eyebrow="Архив" title="Архив документов">
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}
      {isError ? <Alert tone="danger">Не удалось загрузить архив.</Alert> : null}
      <Card>
        <div className="toolbar archive-toolbar">
          <label className="compact-field">
            Тип
            <select
              value={filters.document_type}
              onChange={(event) => updateFilter("document_type", event.target.value)}
            >
              {DOCUMENT_TYPE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="compact-field">
            Формат
            <select
              value={filters.file_format}
              onChange={(event) => updateFilter("file_format", event.target.value)}
            >
              {FILE_FORMAT_OPTIONS.map((option) => (
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
          <label className="compact-field archive-search-field">
            Поиск
            <input
              type="search"
              value={filters.q}
              onChange={(event) => updateFilter("q", event.target.value)}
              placeholder="Название или автор"
            />
          </label>
        </div>
        <DataTable columns={columns} rows={documents} emptyText="В архиве пока нет документов." />
      </Card>
    </PageShell>
  );
}
