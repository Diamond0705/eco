export const ORDER_STATUS_LABELS = {
  new: "Новая",
  calculated: "Рассчитана",
  planned: "Запланирована",
  completed: "Завершена",
  cancelled: "Отменена"
};

export const ORDER_STATUS_OPTIONS = [
  { value: "", label: "Все статусы" },
  { value: "new", label: "Новые" },
  { value: "calculated", label: "Рассчитанные" },
  { value: "planned", label: "Запланированные" },
  { value: "completed", label: "Завершенные" },
  { value: "cancelled", label: "Отмененные" }
];

export const TRIP_STATUS_LABELS = {
  planned: "Запланирован",
  in_progress: "В пути",
  delivered: "Доставлен",
  cancelled: "Отменен"
};

export const TRIP_STATUS_OPTIONS = [
  { value: "", label: "Все статусы" },
  { value: "planned", label: "Запланированные" },
  { value: "in_progress", label: "В пути" },
  { value: "delivered", label: "Доставленные" },
  { value: "cancelled", label: "Отмененные" }
];

export const DOCUMENT_TYPE_LABELS = {
  waybill_pdf: "Путевой лист PDF",
  emissions_pdf: "Отчет по выбросам PDF",
  emissions_xlsx: "Отчет по выбросам Excel",
  admin_analytics_xlsx: "Сводка компании Excel",
  trips_xlsx: "Экспорт рейсов Excel"
};

export const DOCUMENT_TYPE_OPTIONS = [
  { value: "", label: "Все документы" },
  { value: "waybill_pdf", label: "Путевые листы" },
  { value: "emissions_pdf", label: "Отчеты PDF" },
  { value: "emissions_xlsx", label: "Отчеты Excel" },
  { value: "trips_xlsx", label: "Экспорт рейсов" },
  { value: "admin_analytics_xlsx", label: "Сводки компании" }
];

export const FILE_FORMAT_OPTIONS = [
  { value: "", label: "Все форматы" },
  { value: "pdf", label: "PDF" },
  { value: "xlsx", label: "XLSX" }
];

export function formatDate(value) {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU").format(new Date(value));
}

export function formatDateTime(value) {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU", {
    dateStyle: "short",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatNumber(value, options = {}) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  return new Intl.NumberFormat("ru-RU", options).format(Number(value));
}

export function formatWeight(value) {
  return `${formatNumber(value, { maximumFractionDigits: 0 })} кг`;
}

export function formatDistance(value) {
  return `${formatNumber(value, { maximumFractionDigits: 2 })} км`;
}

export function formatMoney(value) {
  return `${formatNumber(value, { maximumFractionDigits: 2 })} ₽`;
}

export function formatFuel(value) {
  return `${formatNumber(value, { maximumFractionDigits: 2 })} л`;
}

export function formatEmissions(value, unit = "кг") {
  return `${formatNumber(value, { maximumFractionDigits: unit === "г" ? 3 : 2 })} ${unit}`;
}

export function formatDuration(value) {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  const minutes = Number(value);
  const hours = Math.floor(minutes / 60);
  const rest = minutes % 60;
  if (!hours) {
    return `${rest} мин`;
  }
  return `${hours} ч ${rest} мин`;
}

export function formatBytes(value) {
  if (!value) {
    return "—";
  }
  const bytes = Number(value);
  if (bytes < 1024 * 1024) {
    return `${formatNumber(bytes / 1024, { maximumFractionDigits: 1 })} КБ`;
  }
  return `${formatNumber(bytes / (1024 * 1024), { maximumFractionDigits: 1 })} МБ`;
}

export function transportLabel(transport) {
  if (!transport) {
    return "—";
  }
  return `${transport.plate_number} — ${transport.model}`;
}

export function locationLabel(location) {
  if (!location) {
    return "—";
  }
  return `${location.name}${location.address ? `, ${location.address}` : ""}`;
}

export function orderStatusLabel(status) {
  return ORDER_STATUS_LABELS[status] || status || "—";
}

export function tripStatusLabel(status) {
  return TRIP_STATUS_LABELS[status] || status || "—";
}

export function documentTypeLabel(type, fallback) {
  return fallback || DOCUMENT_TYPE_LABELS[type] || type || "—";
}

export function canCancelOrder(order) {
  return ["new", "calculated"].includes(order?.status) && !order?.trip;
}
