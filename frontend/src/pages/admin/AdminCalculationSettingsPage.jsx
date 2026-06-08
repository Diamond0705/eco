import { useEffect, useState } from "react";

import {
  useAdminCalculationSettingsQuery,
  useCreateAdminCalculationSettingsMutation
} from "../../api/adminApi.js";
import Alert from "../../components/ui/Alert.jsx";
import Badge from "../../components/ui/Badge.jsx";
import Card from "../../components/ui/Card.jsx";
import DataTable from "../../components/ui/DataTable.jsx";
import LoadingState from "../../components/ui/LoadingState.jsx";
import { formatDateTime } from "../../utils/formatters.js";

const SETTINGS_FIELDS = [
  { name: "name", label: "Название версии", type: "text" },
  { name: "fuel_price_rub_per_liter", label: "Цена топлива, руб/л" },
  { name: "service_tariff_rub_per_km", label: "Сервисный тариф, руб/км" },
  { name: "driver_time_tariff_rub_per_hour", label: "Тариф времени водителя, руб/ч" },
  { name: "diesel_co2_kg_per_liter", label: "CO2 дизеля, кг/л" },
  { name: "engine_work_kwh_per_km", label: "Работа двигателя, кВт·ч/км" },
  { name: "full_load_fuel_increase_percent", label: "Рост расхода при полной загрузке, %" },
  { name: "co2_weight", label: "Вес CO2" },
  { name: "nox_weight", label: "Вес NOx" },
  { name: "pm_weight", label: "Вес PM" },
  { name: "co2_critical_kg", label: "Критический CO2, кг" },
  { name: "nox_critical_g", label: "Критический NOx, г" },
  { name: "pm_critical_g", label: "Критический PM, г" }
];

function formFromSettings(settings) {
  if (!settings) {
    return {
      name: "",
      is_active: true
    };
  }
  return SETTINGS_FIELDS.reduce(
    (values, field) => ({
      ...values,
      [field.name]:
        field.name === "name" ? `${settings.name} новая версия` : settings[field.name] ?? ""
    }),
    { is_active: true }
  );
}

function errorMessage(error) {
  if (!error?.data) {
    return "Не удалось сохранить настройки.";
  }
  if (typeof error.data.detail === "string") {
    return error.data.detail;
  }
  return Object.entries(error.data)
    .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join("; ");
}

export default function AdminCalculationSettingsPage() {
  const { data, isError, isLoading } = useAdminCalculationSettingsQuery();
  const [createSettings, createState] = useCreateAdminCalculationSettingsMutation();
  const [form, setForm] = useState(formFromSettings(null));

  useEffect(() => {
    if (data?.current) {
      setForm(formFromSettings(data.current));
    }
  }, [data?.current]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    await createSettings({ ...form, is_active: true }).unwrap();
  };

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError) {
    return <Alert tone="danger">Не удалось загрузить настройки экорасчета.</Alert>;
  }

  return (
    <section className="admin-page">
      <div className="admin-page-heading">
        <div>
          <h1>Экорасчет</h1>
          <p>Версии настроек применяются только к новым расчетам маршрутов.</p>
        </div>
      </div>

      {createState.isSuccess ? <Alert tone="success">Создана новая активная версия настроек.</Alert> : null}
      {createState.error ? <Alert tone="danger">{errorMessage(createState.error)}</Alert> : null}

      <div className="admin-settings-layout">
        <Card className="admin-form-card">
          <h2>Новая активная версия</h2>
          <form className="admin-form admin-settings-form" onSubmit={handleSubmit}>
            {SETTINGS_FIELDS.map((field) => (
              <label key={field.name} className="form-field">
                {field.label}
                <input
                  type={field.type || "number"}
                  step={field.type === "text" ? undefined : "0.01"}
                  value={form[field.name] ?? ""}
                  onChange={(event) =>
                    setForm((current) => ({ ...current, [field.name]: event.target.value }))
                  }
                  required
                />
              </label>
            ))}
            <div className="form-actions">
              <button type="submit" disabled={createState.isLoading}>
                {createState.isLoading ? "Сохраняем..." : "Сохранить новую версию"}
              </button>
            </div>
          </form>
        </Card>

        <Card>
          <h2>История версий</h2>
          <DataTable
            rows={data?.versions || []}
            emptyText="Версии настроек не найдены."
            columns={[
              { key: "name", label: "Название" },
              {
                key: "is_active",
                label: "Статус",
                render: (row) => (
                  <Badge tone={row.is_active ? "success" : "neutral"}>
                    {row.is_active ? "Активна" : "Неактивна"}
                  </Badge>
                )
              },
              { key: "fuel_price_rub_per_liter", label: "Топливо" },
              { key: "service_tariff_rub_per_km", label: "Тариф/км" },
              { key: "diesel_co2_kg_per_liter", label: "CO2 дизеля" },
              {
                key: "updated_at",
                label: "Обновлена",
                render: (row) => formatDateTime(row.updated_at)
              }
            ]}
          />
        </Card>
      </div>
    </section>
  );
}
