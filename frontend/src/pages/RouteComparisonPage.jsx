import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  useApproveRouteMutation,
  useCalculateRoutesMutation,
  useOrderQuery,
  useRouteOptionsQuery
} from "../api/managerApi.js";
import RouteMap from "../components/routes/RouteMap.jsx";
import RouteOptionCard from "../components/routes/RouteOptionCard.jsx";
import Alert from "../components/ui/Alert.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import EmptyState from "../components/ui/EmptyState.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import { formatDate, formatWeight, locationLabel, transportLabel } from "../utils/formatters.js";

export default function RouteComparisonPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const { data: order, isError: isOrderError, isLoading: isOrderLoading } = useOrderQuery(id);
  const {
    data: routes = [],
    isError: isRoutesError,
    isFetching: isRoutesFetching,
    refetch
  } = useRouteOptionsQuery(id);
  const [calculateRoutes, { isLoading: isCalculating }] = useCalculateRoutesMutation();
  const [approveRoute, { isLoading: isApproving }] = useApproveRouteMutation();
  const pickup = order?.points?.find((point) => point.point_type === "pickup");
  const delivery = order?.points?.find((point) => point.point_type === "delivery");
  const validRoutes = useMemo(
    () => routes.filter((route) => Array.isArray(route.geometry_json) && route.geometry_json.length > 1),
    [routes]
  );

  const handleCalculate = async () => {
    setMessage("");
    setErrorMessage("");
    try {
      await calculateRoutes({ orderId: id }).unwrap();
      await refetch();
      setMessage("Маршруты рассчитаны.");
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось рассчитать маршруты.");
    }
  };

  const handleApprove = async (route) => {
    setMessage("");
    setErrorMessage("");
    try {
      const trip = await approveRoute({ orderId: id, routeOptionId: route.id }).unwrap();
      navigate(`/orders/${id}`, {
        state: {
          message: `Маршрут утвержден. Создан рейс №${trip.id}.`
        }
      });
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось утвердить маршрут.");
    }
  };

  if (isOrderLoading) {
    return <LoadingState />;
  }

  if (isOrderError || !order) {
    return <Alert tone="danger">Не удалось загрузить данные заявки.</Alert>;
  }

  return (
    <PageShell
      eyebrow="Маршруты"
      title="Сравнение маршрутов"
      actions={<Button to={`/orders/${id}`} variant="secondary">К заявке</Button>}
    >
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}
      <section className="route-layout">
        <Card className="route-summary-card">
          <p className="eyebrow">Заявка №{order.id}</p>
          <h2>{order.cargo_name}</h2>
          <dl className="detail-list">
            <div>
              <dt>Груз</dt>
              <dd>
                {order.cargo_type}, {formatWeight(order.cargo_weight_kg)}
              </dd>
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
              <dt>Отправление</dt>
              <dd>{locationLabel(pickup?.location)}</dd>
            </div>
            <div>
              <dt>Доставка</dt>
              <dd>{locationLabel(delivery?.location)}</dd>
            </div>
          </dl>
          {["new", "calculated"].includes(order.status) ? (
            <Button disabled={isCalculating} onClick={handleCalculate}>
              {isCalculating ? "Расчет маршрутов..." : "Рассчитать маршруты"}
            </Button>
          ) : null}
        </Card>

        <Card className="map-card">
          {isRoutesFetching ? <LoadingState text="Загрузка маршрутов..." /> : null}
          {validRoutes.length ? (
            <RouteMap routes={validRoutes} />
          ) : (
            <EmptyState title="Маршруты не найдены">
              Рассчитайте маршруты для заявки, чтобы увидеть варианты на карте.
            </EmptyState>
          )}
        </Card>
      </section>

      {isRoutesError ? <Alert tone="danger">Не удалось загрузить маршруты.</Alert> : null}

      <section className="route-options-list">
        {routes.length ? (
          routes.map((route) => (
            <RouteOptionCard
              key={route.id}
              route={route}
              isApproving={isApproving}
              onApprove={handleApprove}
            />
          ))
        ) : (
          <EmptyState title="Нет вариантов маршрута">
            Нажмите «Рассчитать маршруты», чтобы получить варианты для сравнения.
          </EmptyState>
        )}
      </section>
    </PageShell>
  );
}
