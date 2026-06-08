import { useState } from "react";
import { useParams } from "react-router-dom";

import {
  useArchiveWaybillMutation,
  useDeliverTripMutation,
  useDownloadWaybillMutation,
  useStartTripMutation,
  useTripQuery
} from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { saveDownload } from "../utils/downloads.js";
import {
  formatDateTime,
  formatDistance,
  formatDuration,
  formatEmissions,
  formatFuel,
  formatMoney,
  tripStatusLabel,
  transportLabel
} from "../utils/formatters.js";

const statusTone = {
  planned: "info",
  in_progress: "success",
  delivered: "neutral",
  cancelled: "danger"
};

function toIsoDateTime(value) {
  return value ? new Date(value).toISOString() : undefined;
}

export default function TripDetailPage() {
  const { id } = useParams();
  const [actionForm, setActionForm] = useState({ event_at: "", comment: "" });
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { data: trip, isError, isLoading } = useTripQuery(id);
  const [startTrip, { isLoading: isStarting }] = useStartTripMutation();
  const [deliverTrip, { isLoading: isDelivering }] = useDeliverTripMutation();
  const [downloadWaybill, { isLoading: isDownloading }] = useDownloadWaybillMutation();
  const [archiveWaybill, { isLoading: isArchiving }] = useArchiveWaybillMutation();

  const handleLifecycle = async (action) => {
    setMessage("");
    setErrorMessage("");
    const payload =
      action === "start"
        ? { id, actual_start: toIsoDateTime(actionForm.event_at), comment: actionForm.comment }
        : { id, actual_finish: toIsoDateTime(actionForm.event_at), comment: actionForm.comment };
    try {
      if (action === "start") {
        await startTrip(payload).unwrap();
        setMessage("Рейс переведен в статус «В пути».");
      } else {
        await deliverTrip(payload).unwrap();
        setMessage("Рейс завершен.");
      }
      setActionForm({ event_at: "", comment: "" });
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось изменить статус рейса.");
    }
  };

  const handleWaybillDownload = async () => {
    setMessage("");
    setErrorMessage("");
    try {
      saveDownload(await downloadWaybill(id).unwrap());
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось скачать путевой лист.");
    }
  };

  const handleWaybillArchive = async () => {
    setMessage("");
    setErrorMessage("");
    try {
      await archiveWaybill(id).unwrap();
      setMessage("Путевой лист сохранен в архив.");
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось сохранить путевой лист в архив.");
    }
  };

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError || !trip) {
    return <Alert tone="danger">Не удалось загрузить данные рейса.</Alert>;
  }

  const route = trip.route_option;
  const canStart = trip.status === "planned";
  const canDeliver = trip.status === "in_progress";

  return (
    <PageShell
      eyebrow="Рейс"
      title={`Рейс №${trip.id}`}
      actions={<Button to="/trips" variant="secondary">К списку рейсов</Button>}
    >
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}

      <section className="detail-grid">
        <Card>
          <div className="detail-heading">
            <div>
              <h2>{trip.order?.cargo_name || "Рейс"}</h2>
              <p>{transportLabel(trip.transport)}</p>
            </div>
            <Badge tone={statusTone[trip.status] || "neutral"}>{tripStatusLabel(trip.status)}</Badge>
          </div>
          <dl className="detail-list">
            <div>
              <dt>Плановый старт</dt>
              <dd>{formatDateTime(trip.planned_start)}</dd>
            </div>
            <div>
              <dt>Фактический старт</dt>
              <dd>{formatDateTime(trip.actual_start)}</dd>
            </div>
            <div>
              <dt>Фактическое завершение</dt>
              <dd>{formatDateTime(trip.actual_finish)}</dd>
            </div>
            <div>
              <dt>Менеджер</dt>
              <dd>{trip.manager?.full_name || trip.manager?.username || "—"}</dd>
            </div>
          </dl>
        </Card>

        <Card>
          <h2>Маршрут и расчет</h2>
          <dl className="detail-list">
            <div>
              <dt>Маршрут</dt>
              <dd>{route?.name || "—"}</dd>
            </div>
            <div>
              <dt>Расстояние</dt>
              <dd>{formatDistance(route?.distance_km)}</dd>
            </div>
            <div>
              <dt>Время</dt>
              <dd>{formatDuration(route?.duration_minutes)}</dd>
            </div>
            <div>
              <dt>Стоимость</dt>
              <dd>{formatMoney(route?.cost_rub)}</dd>
            </div>
            <div>
              <dt>Топливо</dt>
              <dd>{formatFuel(route?.fuel_liters)}</dd>
            </div>
            <div>
              <dt>CO2</dt>
              <dd>{formatEmissions(route?.co2_kg, "кг")}</dd>
            </div>
            <div>
              <dt>NOx / PM</dt>
              <dd>
                {formatEmissions(route?.nox_g, "г")} / {formatEmissions(route?.pm_g, "г")}
              </dd>
            </div>
          </dl>
        </Card>
      </section>

      <Card className="actions-card">
        <h2>Действия по рейсу</h2>
        {(canStart || canDeliver) ? (
          <div className="lifecycle-form">
            <label className="form-field">
              Фактическое время
              <input
                type="datetime-local"
                value={actionForm.event_at}
                onChange={(event) =>
                  setActionForm((current) => ({ ...current, event_at: event.target.value }))
                }
              />
              <span className="field-hint">Если оставить пустым, сервер возьмет текущее время.</span>
            </label>
            <label className="form-field form-field-wide">
              Комментарий
              <textarea
                value={actionForm.comment}
                onChange={(event) =>
                  setActionForm((current) => ({ ...current, comment: event.target.value }))
                }
              />
            </label>
          </div>
        ) : null}
        <div className="form-actions">
          {canStart ? (
            <Button disabled={isStarting} onClick={() => handleLifecycle("start")}>
              {isStarting ? "Запускаем..." : "Начать рейс"}
            </Button>
          ) : null}
          {canDeliver ? (
            <Button disabled={isDelivering} onClick={() => handleLifecycle("deliver")}>
              {isDelivering ? "Завершаем..." : "Завершить рейс"}
            </Button>
          ) : null}
          <Button variant="secondary" disabled={isDownloading} onClick={handleWaybillDownload}>
            {isDownloading ? "Готовим PDF..." : "Скачать путевой лист"}
          </Button>
          <Button variant="secondary" disabled={isArchiving} onClick={handleWaybillArchive}>
            {isArchiving ? "Сохраняем..." : "Путевой лист в архив"}
          </Button>
        </div>
      </Card>

      <Card>
        <h2>История статусов</h2>
        <ol className="timeline-list">
          {(trip.status_events || []).map((event) => (
            <li key={event.id}>
              <span>{formatDateTime(event.changed_at)}</span>
              <strong>
                {tripStatusLabel(event.old_status)} → {tripStatusLabel(event.new_status)}
              </strong>
              {event.comment ? <p>{event.comment}</p> : null}
            </li>
          ))}
        </ol>
      </Card>
    </PageShell>
  );
}
