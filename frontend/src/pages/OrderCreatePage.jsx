import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  useCreateOrderMutation,
  useLocationsQuery,
  useTransportsQuery
} from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
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
      eyebrow="Новая заявка"
      title="Создать заявку на перевозку"
      actions={<Button to="/orders" variant="secondary">К списку</Button>}
    >
      {error ? <Alert tone="danger">Проверьте данные заявки.</Alert> : null}
      <Card>
        <form className="order-form" onSubmit={handleSubmit}>
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
          <label className="form-field form-field-wide">
            <span>Примечания</span>
            <textarea name="notes" value={form.notes} onChange={handleChange} rows="4" />
          </label>
          <div className="form-actions">
            <Button type="submit" disabled={isSaving}>
              {isSaving ? "Сохраняем..." : "Создать заявку"}
            </Button>
            <Button to="/orders" variant="secondary">
              Отмена
            </Button>
          </div>
        </form>
      </Card>
    </PageShell>
  );
}
