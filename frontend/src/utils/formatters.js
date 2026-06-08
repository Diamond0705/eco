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

export function formatDate(value) {
  if (!value) {
    return "—";
  }
  return new Intl.DateTimeFormat("ru-RU").format(new Date(value));
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

export function canCancelOrder(order) {
  return ["new", "calculated"].includes(order?.status) && !order?.trip;
}
