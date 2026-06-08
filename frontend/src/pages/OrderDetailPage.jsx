import { useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

import { useCancelOrderMutation, useOrderQuery } from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import {
  canCancelOrder,
  formatDate,
  formatWeight,
  locationLabel,
  orderStatusLabel,
  transportLabel
} from "../utils/formatters.js";

const statusTone = {
  new: "info",
  calculated: "success",
  planned: "success",
  completed: "neutral",
  cancelled: "danger"
};

export default function OrderDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [message, setMessage] = useState(location.state?.message || "");
  const { data: order, isError, isLoading } = useOrderQuery(id);
  const [cancelOrder, { isLoading: isCancelling }] = useCancelOrderMutation();

  const handleCancel = async () => {
    if (!window.confirm("Отменить заявку?")) {
      return;
    }
    await cancelOrder(id).unwrap();
    setMessage("Заявка отменена.");
  };

  if (isLoading) {
    return <LoadingState />;
  }

  if (isError || !order) {
    return <Alert tone="danger">Не удалось загрузить данные заявки.</Alert>;
  }

  const pickup = order.points?.find((point) => point.point_type === "pickup");
  const delivery = order.points?.find((point) => point.point_type === "delivery");

  return (
    <PageShell
      eyebrow="Заявка"
      title={`Заявка №${order.id}`}
      actions={<Button to="/orders" variant="secondary">К списку</Button>}
    >
      {message ? <Alert tone="success">{message}</Alert> : null}
      <section className="detail-grid">
        <Card>
          <div className="detail-heading">
            <div>
              <h2>{order.cargo_name}</h2>
              <p>{order.cargo_type}</p>
            </div>
            <Badge tone={statusTone[order.status] || "neutral"}>{orderStatusLabel(order.status)}</Badge>
          </div>
          <dl className="detail-list">
            <div>
              <dt>Вес</dt>
              <dd>{formatWeight(order.cargo_weight_kg)}</dd>
            </div>
            <div>
              <dt>Транспорт</dt>
              <dd>{transportLabel(order.transport)}</dd>
            </div>
            <div>
              <dt>Дата доставки</dt>
              <dd>{formatDate(order.delivery_date)}</dd>
            </div>
            <div>
              <dt>Примечания</dt>
              <dd>{order.notes || "—"}</dd>
            </div>
          </dl>
        </Card>

        <Card>
          <h2>Точки маршрута</h2>
          <ol className="points-list">
            <li>
              <span>Отправление</span>
              <strong>{locationLabel(pickup?.location)}</strong>
            </li>
            <li>
              <span>Доставка</span>
              <strong>{locationLabel(delivery?.location)}</strong>
            </li>
          </ol>
        </Card>
      </section>

      <Card className="actions-card">
        <h2>Действия</h2>
        <div className="form-actions">
          {["new", "calculated"].includes(order.status) ? (
            <Button to={`/orders/${order.id}/routes`}>
              {order.route_options?.length ? "Сравнить маршруты" : "Рассчитать маршруты"}
            </Button>
          ) : null}
          {canCancelOrder(order) ? (
            <Button variant="danger" disabled={isCancelling} onClick={handleCancel}>
              {isCancelling ? "Отменяем..." : "Отменить заявку"}
            </Button>
          ) : null}
          <Button variant="secondary" onClick={() => navigate("/orders")}>
            Назад к списку
          </Button>
          {order.route_options?.length ? (
            <Link className="button button-secondary" to={`/orders/${order.id}/routes`}>
              Открыть варианты маршрута
            </Link>
          ) : null}
        </div>
      </Card>
    </PageShell>
  );
}
