const detailLabels = {
  calculation_model_version: "Модель расчета",
  final_fuel_multiplier: "Итоговый множитель топлива",
  average_speed_kmh: "Средняя скорость, км/ч",
  road_class_factor: "Коэффициент класса дороги",
  surface_factor: "Коэффициент покрытия",
  traffic_factor: "Коэффициент пробок"
};

export default function RouteCalculationDetails({ details }) {
  if (!details) {
    return null;
  }

  return (
    <details className="calculation-details">
      <summary>Как рассчитан маршрут</summary>
      <dl>
        {Object.entries(detailLabels).map(([key, label]) => (
          <div key={key}>
            <dt>{label}</dt>
            <dd>{details[key] ?? "—"}</dd>
          </div>
        ))}
      </dl>
    </details>
  );
}
