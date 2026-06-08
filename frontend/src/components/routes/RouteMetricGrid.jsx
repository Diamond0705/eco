import { formatDistance, formatNumber } from "../../utils/formatters.js";

function durationLabel(minutes) {
  const value = Number(minutes);
  if (!Number.isFinite(value)) {
    return "—";
  }
  const hours = Math.floor(value / 60);
  const rest = value % 60;
  if (!hours) {
    return `${rest} мин`;
  }
  return `${hours} ч ${rest} мин`;
}

export default function RouteMetricGrid({ route }) {
  const metrics = [
    { label: "Расстояние", value: formatDistance(route.distance_km) },
    { label: "Время", value: durationLabel(route.duration_minutes) },
    { label: "Топливо", value: `${formatNumber(route.fuel_liters, { maximumFractionDigits: 2 })} л` },
    { label: "Стоимость", value: `${formatNumber(route.cost_rub, { maximumFractionDigits: 2 })} ₽` },
    { label: "CO2", value: `${formatNumber(route.co2_kg, { maximumFractionDigits: 2 })} кг` },
    { label: "NOx", value: `${formatNumber(route.nox_g, { maximumFractionDigits: 2 })} г` },
    { label: "PM", value: `${formatNumber(route.pm_g, { maximumFractionDigits: 3 })} г` },
    { label: "Эко-рейтинг", value: formatNumber(route.eco_rating, { maximumFractionDigits: 2 }) }
  ];

  return (
    <div className="route-metric-grid">
      {metrics.map((metric) => (
        <div key={metric.label}>
          <span>{metric.label}</span>
          <strong>{metric.value}</strong>
        </div>
      ))}
    </div>
  );
}
