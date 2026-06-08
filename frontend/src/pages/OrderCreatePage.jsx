import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  useCreateOrderMutation,
  useLocationsQuery,
  useTransportsQuery
} from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Button from "../components/ui/Button.jsx";
import FormField from "../components/ui/FormField.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { formatWeight, locationLabel, transportLabel } from "../utils/formatters.js";

const initialForm = {
  cargo_name: "",
  cargo_type: "",
  cargo_weight_kg: "",
  transport: "",
  delivery_date: "",
  notes: "",
  origin_location: "",
  destination_location: ""
};

function fieldError(error, name) {
  const value = error?.data?.[name];
  if (Array.isArray(value)) {
    return value.join(" ");
  }
  return value || "";
}

function SectionIcon({ type }) {
  const paths = {
    cargo: (
      <>
        <path d="M12 3 4.5 7.2v8.6L12 20l7.5-4.2V7.2L12 3Z" />
        <path d="m4.8 7.4 7.2 4 7.2-4" />
        <path d="M12 11.4V20" />
      </>
    ),
    transport: (
      <>
        <path d="M3 7h11v10H3z" />
        <path d="M14 10h3.5l2.5 3v4h-6z" />
        <path d="M6.5 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
        <path d="M17.5 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />
      </>
    ),
    route: (
      <>
        <path d="M12 21s6-5.4 6-11a6 6 0 0 0-12 0c0 5.6 6 11 6 11Z" />
        <path d="M12 12.2a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4Z" />
      </>
    )
  };

  return (
    <span className="order-form-section-icon" aria-hidden="true">
      <svg viewBox="0 0 24 24">{paths[type]}</svg>
    </span>
  );
}

export default function OrderCreatePage() {
  const navigate = useNavigate();
  const [form, setForm] = useState(initialForm);
  const [createOrder, { error, isLoading: isSaving }] = useCreateOrderMutation();
  const { data: transports = [], isLoading: isTransportsLoading } = useTransportsQuery();
  const { data: locations = [], isLoading: isLocationsLoading } = useLocationsQuery();
  const selectedTransport = useMemo(
    () => transports.find((transport) => String(transport.id) === String(form.transport)),
    [form.transport, transports]
  );
  const cargoWeight = Number(form.cargo_weight_kg);
  const capacity = Number(selectedTransport?.capacity_kg);
  const capacityMessage =
    selectedTransport && cargoWeight
      ? cargoWeight <= capacity
        ? `Подходит для груза ${formatWeight(cargoWeight)}`
        : `Груз превышает грузоподъемность ${formatWeight(capacity)}`
      : selectedTransport
        ? `Грузоподъемность: ${formatWeight(capacity)}`
        : "";

  const handleChange = (event) => {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      const order = await createOrder(form).unwrap();
      navigate(`/orders/${order.id}`, { state: { message: "Заявка создана." } });
    } catch {
      // RTK Query exposes field errors for the form.
    }
  };

  if (isTransportsLoading || isLocationsLoading) {
    return <LoadingState />;
  }

  return (
    <PageShell
      className="order-create-panel"
      title="Создание заявки"
      subtitle="Укажите характеристики груза, затем подберите подходящий транспорт и маршрут."
      variant="form"
    >
      {error ? <Alert tone="danger">Проверьте данные заявки.</Alert> : null}
      <form className="order-create-form" onSubmit={handleSubmit}>
        <section className="order-form-section">
          <h2 className="order-form-section-title">
            <SectionIcon type="cargo" />
            Данные о грузе
          </h2>
          <div className="order-form-grid order-form-grid-three">
          <FormField
            label="Наименование груза"
            name="cargo_name"
            value={form.cargo_name}
            onChange={handleChange}
            error={fieldError(error, "cargo_name")}
            required
          />
          <FormField
            label="Тип груза"
            name="cargo_type"
            value={form.cargo_type}
            onChange={handleChange}
            error={fieldError(error, "cargo_type")}
            required
          />
          <FormField
            label="Вес груза, кг"
            name="cargo_weight_kg"
            type="number"
            min="0.01"
            step="0.01"
            value={form.cargo_weight_kg}
            onChange={handleChange}
            error={fieldError(error, "cargo_weight_kg")}
            required
          />
          </div>
        </section>

        <section className="order-form-section">
          <h2 className="order-form-section-title">
            <SectionIcon type="transport" />
            Выбор транспорта
          </h2>
          <div className="order-form-grid order-form-grid-two">
          <FormField label="Транспорт" error={fieldError(error, "transport")}>
            <select name="transport" value={form.transport} onChange={handleChange} required>
              <option value="">Выберите транспорт</option>
              {transports.map((transport) => (
                <option key={transport.id} value={transport.id}>
                  {transportLabel(transport)}
                </option>
              ))}
            </select>
            {capacityMessage ? <small className="field-hint">{capacityMessage}</small> : null}
          </FormField>
          <FormField
            label="Желаемая дата доставки"
            name="delivery_date"
            type="date"
            value={form.delivery_date}
            onChange={handleChange}
            error={fieldError(error, "delivery_date")}
            required
          />
          <label className="form-field form-field-wide">
            <span>Примечания</span>
            <textarea name="notes" value={form.notes} onChange={handleChange} rows="4" />
          </label>
          </div>
        </section>

        <section className="order-form-section order-form-section-last">
          <h2 className="order-form-section-title">
            <SectionIcon type="route" />
            Маршрут
          </h2>
          <div className="order-form-grid order-form-grid-two">
          <FormField label="Точка отправления" error={fieldError(error, "origin_location")}>
            <select
              name="origin_location"
              value={form.origin_location}
              onChange={handleChange}
              required
            >
              <option value="">Выберите точку</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {locationLabel(location)}
                </option>
              ))}
            </select>
          </FormField>
          <FormField label="Точка доставки" error={fieldError(error, "destination_location")}>
            <select
              name="destination_location"
              value={form.destination_location}
              onChange={handleChange}
              required
            >
              <option value="">Выберите точку</option>
              {locations.map((location) => (
                <option key={location.id} value={location.id}>
                  {locationLabel(location)}
                </option>
              ))}
            </select>
          </FormField>
          </div>
        </section>

          <div className="order-create-actions">
            <Button type="submit" disabled={isSaving} className="order-create-button order-create-button-primary">
              {isSaving ? "Сохраняем..." : "Создать заявку"}
            </Button>
            <Button to="/orders" variant="secondary" className="order-create-button order-create-button-secondary">
              Отмена
            </Button>
          </div>
        </form>
    </PageShell>
  );
}
