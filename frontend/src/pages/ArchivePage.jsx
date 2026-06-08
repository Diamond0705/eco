import { useState } from "react";

import {
  useArchiveDocumentsQuery,
  useDeleteArchiveDocumentMutation,
  useDownloadArchiveDocumentMutation
} from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import DataTable from "../components/ui/DataTable.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { saveDownload } from "../utils/downloads.js";
import {
  DOCUMENT_TYPE_OPTIONS,
  FILE_FORMAT_OPTIONS,
  documentTypeLabel,
  formatBytes,
  formatDateTime
} from "../utils/formatters.js";

function userLabel(user) {
  if (!user) {
    return "Компания";
  }
  return user.full_name || user.username || "Компания";
}

function ArchiveFileIcon({ format }) {
  const normalized = (format || "").toLowerCase();
  return (
    <span className={`archive-file-icon archive-file-icon-${normalized}`} aria-hidden="true">
      <svg viewBox="0 0 32 38" focusable="false">
        <path d="M5 1h16l7 7v29H5z" />
        <path d="M21 1v8h7" />
        <text x="16" y="27" textAnchor="middle">
          {normalized.toUpperCase() || "DOC"}
        </text>
      </svg>
    </span>
  );
}

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

  const resetFilters = () => {
    setFilters({
      document_type: "",
      file_format: "",
      date_from: "",
      date_to: "",
      q: ""
    });
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
      label: "Название документа",
      render: (document) => (
        <div className="archive-document-title">
          <ArchiveFileIcon format={document.file_format} />
          <span>{document.title}</span>
        </div>
      )
    },
    {
      key: "type",
      label: "Тип",
      render: (document) => documentTypeLabel(document.document_type, document.document_type_display)
    },
    { key: "created", label: "Дата ↓", render: (document) => formatDateTime(document.created_at) },
    { key: "author", label: "Автор", render: (document) => userLabel(document.owner || document.created_by) },
    { key: "size", label: "Размер", render: (document) => formatBytes(document.file_size_bytes) },
    {
      key: "format",
      label: "Формат",
      render: (document) => (
        <span className={`archive-format-badge archive-format-badge-${document.file_format}`}>
          {(document.file_format || document.file_format_display || "").toUpperCase()}
        </span>
      )
    },
    {
      key: "actions",
      label: "Действия",
      render: (document) => (
        <div className="archive-row-actions">
          <button
            className="archive-download-button"
            type="button"
            disabled={isDownloading}
            onClick={() => handleDownload(document)}
          >
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path d="M12 3v11" />
              <path d="m8 10 4 4 4-4" />
              <path d="M5 20h14" />
            </svg>
            Скачать
          </button>
          <button
            className="archive-delete-button"
            type="button"
            disabled={isDeleting}
            onClick={() => handleDelete(document)}
            aria-label={`Удалить ${document.title}`}
            title="Удалить"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
              <path d="M4 7h16" />
              <path d="M10 11v6" />
              <path d="M14 11v6" />
              <path d="M6 7l1 14h10l1-14" />
              <path d="M9 7V4h6v3" />
            </svg>
          </button>
        </div>
      )
    }
  ];

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <PageShell
      className="archive-panel"
      title="Архив документов"
      subtitle="Сохранённые отчёты и документы по рейсам и маршрутам."
      variant="wide"
    >
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}
      {isError ? <Alert tone="danger">Не удалось загрузить архив.</Alert> : null}
      <form className="archive-filter-card" onSubmit={(event) => event.preventDefault()}>
          <label className="archive-filter-field">
            Тип документа
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
          <label className="archive-filter-field archive-period-field">
            Период
            <div className="archive-date-range">
            <input
              type="date"
              value={filters.date_from}
              onChange={(event) => updateFilter("date_from", event.target.value)}
              aria-label="Дата с"
            />
            <span aria-hidden="true">—</span>
            <input
              type="date"
              value={filters.date_to}
              onChange={(event) => updateFilter("date_to", event.target.value)}
              aria-label="Дата по"
            />
            </div>
          </label>
          <label className="archive-filter-field">
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
          <label className="archive-filter-field archive-search-field">
            Поиск
            <input
              type="search"
              value={filters.q}
              onChange={(event) => updateFilter("q", event.target.value)}
              placeholder="Название или автор"
            />
          </label>
          <div className="archive-filter-actions">
            <button type="submit" className="button button-primary archive-apply-button">
              Применить
            </button>
            <button
              type="button"
              className="button button-secondary archive-reset-button"
              onClick={resetFilters}
            >
              Сбросить
            </button>
          </div>
      </form>
      <DataTable
        className="archive-table-wrap"
        columns={columns}
        rows={documents}
        emptyText="В архиве пока нет документов."
      />
    </PageShell>
  );
}
