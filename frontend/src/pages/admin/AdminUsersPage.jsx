import { useState } from "react";

import { useAdminUsersQuery, useUpdateAdminUserMutation } from "../../api/adminApi.js";
import Alert from "../../components/ui/Alert.jsx";
import Badge from "../../components/ui/Badge.jsx";
import Card from "../../components/ui/Card.jsx";
import DataTable from "../../components/ui/DataTable.jsx";
import LoadingState from "../../components/ui/LoadingState.jsx";
import { formatDateTime } from "../../utils/formatters.js";

const ACTIVE_OPTIONS = [
  { value: "", label: "Все" },
  { value: "1", label: "Активные" },
  { value: "0", label: "Неактивные" }
];

function userDisplayName(user) {
  return user.full_name || user.username;
}

export default function AdminUsersPage() {
  const [filters, setFilters] = useState({ q: "", is_active: "" });
  const { data = [], isError, isFetching, isLoading } = useAdminUsersQuery(filters);
  const [updateUser, updateState] = useUpdateAdminUserMutation();

  const toggleActivity = async (user) => {
    await updateUser({ id: user.id, is_active: !user.is_active }).unwrap();
  };

  return (
    <section className="admin-page">
      <div className="admin-page-heading">
        <div>
          <h1>Пользователи</h1>
          <p>Просмотр учетных записей и управление активностью менеджеров.</p>
        </div>
      </div>

      {updateState.error ? (
        <Alert tone="danger">
          {updateState.error.data?.detail || "Не удалось изменить активность пользователя."}
        </Alert>
      ) : null}

      <Card className="admin-filter-card">
        <label className="compact-field">
          Поиск
          <input
            value={filters.q}
            onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
            placeholder="Логин, имя, email или телефон"
          />
        </label>
        <label className="compact-field">
          Активность
          <select
            value={filters.is_active}
            onChange={(event) =>
              setFilters((current) => ({ ...current, is_active: event.target.value }))
            }
          >
            {ACTIVE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </Card>

      <Card>
        {isLoading ? <LoadingState /> : null}
        {isError ? <Alert tone="danger">Не удалось загрузить пользователей.</Alert> : null}
        {!isLoading && !isError ? (
          <DataTable
            rows={data}
            emptyText="Пользователи не найдены."
            columns={[
              {
                key: "username",
                label: "Пользователь",
                render: (user) => (
                  <span className="admin-user-cell">
                    <strong>{userDisplayName(user)}</strong>
                    <span>{user.username}</span>
                  </span>
                )
              },
              { key: "email", label: "Email", render: (user) => user.email || "—" },
              { key: "phone", label: "Телефон", render: (user) => user.phone || "—" },
              { key: "role_display", label: "Роль" },
              {
                key: "is_active",
                label: "Статус",
                render: (user) => (
                  <Badge tone={user.is_active ? "success" : "neutral"}>
                    {user.is_active ? "Активен" : "Неактивен"}
                  </Badge>
                )
              },
              {
                key: "last_login",
                label: "Последний вход",
                render: (user) => formatDateTime(user.last_login)
              },
              {
                key: "actions",
                label: "Действия",
                render: (user) =>
                  user.can_edit_activity ? (
                    <button
                      type="button"
                      className="table-button"
                      disabled={updateState.isLoading}
                      onClick={() => toggleActivity(user)}
                    >
                      {user.is_active ? "Деактивировать" : "Активировать"}
                    </button>
                  ) : (
                    <span className="field-hint">Только через Django Admin</span>
                  )
              }
            ]}
          />
        ) : null}
        {isFetching && !isLoading ? <p className="field-hint">Обновляем данные...</p> : null}
      </Card>
    </section>
  );
}
