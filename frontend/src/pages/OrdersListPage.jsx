import { useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { useOrdersQuery } from "../api/managerApi.js";
import Alert from "../components/ui/Alert.jsx";
import Badge from "../components/ui/Badge.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import DataTable from "../components/ui/DataTable.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";
import {
  ORDER_STATUS_OPTIONS,
  formatDate,
  formatWeight,
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

export default function OrdersListPage() {
  const [selectedStatus, setSelectedStatus] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const { data: orders = [], isError, isLoading } = useOrdersQuery();
  const filteredOrders = useMemo(() => {
    if (!statusFilter) {
      return orders;
    }
    return orders.filter((order) => order.status === statusFilter);
  }, [orders, statusFilter]);

  const applyFilters = (event) => {
    event.preventDefault();
    setStatusFilter(selectedStatus);
  };

  const columns = [
    { key: "id", label: "№", render: (order) => <Link to={`/orders/${order.id}`}>#{order.id}</Link> },
    { key: "cargo_name", label: "Груз" },
    { key: "cargo_weight_kg", label: "Вес, кг", render: (order) => formatWeight(order.cargo_weight_kg) },
    { key: "transport", label: "Транспорт", render: (order) => transportLabel(order.transport) },
    { key: "delivery_date", label: "Дата доставки", render: (order) => formatDate(order.delivery_date) },
    {
      key: "status",
      label: "Статус",
      render: (order) => (
        <Badge tone={statusTone[order.status] || "neutral"}>{orderStatusLabel(order.status)}</Badge>
      )
    },
    {
      key: "actions",
      label: "Действие",
      render: (order) => (
        <Link className="table-action" to={`/orders/${order.id}`}>
          Открыть
        </Link>
      )
    }
  ];

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <PageShell
      title="Заявки"
      subtitle="Заявки на перевозку текущего менеджера"
      className="orders-list-panel"
      variant="wide"
      actions={<Button to="/orders/create">Создать заявку</Button>}
    >
      {isError ? <Alert tone="danger">Не удалось загрузить данные.</Alert> : null}
      <Card className="orders-list-card">
        <form className="orders-filter-form" onSubmit={applyFilters}>
          <label htmlFor="order-status">Статус</label>
          <select
            id="order-status"
            value={selectedStatus}
            onChange={(event) => setSelectedStatus(event.target.value)}
          >
            {ORDER_STATUS_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
          <Button type="submit" variant="secondary">
            Показать
          </Button>
        </form>
        <DataTable
          columns={columns}
          rows={filteredOrders}
          emptyText="Заявок пока нет. Создайте первую заявку, чтобы рассчитать маршруты и запланировать рейс."
          className="orders-table-wrap"
        />
      </Card>
    </PageShell>
  );
}
