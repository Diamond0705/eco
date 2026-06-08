import { useMemo, useState } from "react";

import Alert from "../../components/ui/Alert.jsx";
import Button from "../../components/ui/Button.jsx";
import Card from "../../components/ui/Card.jsx";
import DataTable from "../../components/ui/DataTable.jsx";
import LoadingState from "../../components/ui/LoadingState.jsx";

const ACTIVE_OPTIONS = [
  { value: "", label: "Все" },
  { value: "1", label: "Активные" },
  { value: "0", label: "Неактивные" }
];

function errorMessage(error) {
  if (!error?.data) {
    return "Не удалось сохранить данные.";
  }
  if (typeof error.data.detail === "string") {
    return error.data.detail;
  }
  return Object.entries(error.data)
    .map(([field, value]) => `${field}: ${Array.isArray(value) ? value.join(", ") : value}`)
    .join("; ");
}

function fieldValue(item, name, fallback) {
  return item?.[name] ?? fallback ?? "";
}

export default function AdminReferencePage({
  title,
  description,
  emptyText,
  fields,
  columns,
  defaultValues,
  useListQuery,
  useCreateMutation,
  useUpdateMutation,
  normalizePayload = (payload) => payload
}) {
  const [filters, setFilters] = useState({ q: "", is_active: "" });
  const [editingItem, setEditingItem] = useState(null);
  const [form, setForm] = useState(defaultValues);
  const { data = [], isError, isFetching, isLoading } = useListQuery(filters);
  const [createItem, createState] = useCreateMutation();
  const [updateItem, updateState] = useUpdateMutation();
  const isSaving = createState.isLoading || updateState.isLoading;
  const saveError = createState.error || updateState.error;

  const preparedColumns = useMemo(
    () => [
      ...columns,
      {
        key: "actions",
        label: "Действия",
        render: (row) => (
          <button
            type="button"
            className="table-button"
            onClick={() => {
              setEditingItem(row);
              setForm(
                fields.reduce(
                  (values, field) => ({
                    ...values,
                    [field.name]: fieldValue(row, field.name, defaultValues[field.name])
                  }),
                  {}
                )
              );
            }}
          >
            Изменить
          </button>
        )
      }
    ],
    [columns, defaultValues, fields]
  );

  const resetForm = () => {
    setEditingItem(null);
    setForm(defaultValues);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const payload = normalizePayload(form);
    if (editingItem) {
      await updateItem({ id: editingItem.id, ...payload }).unwrap();
    } else {
      await createItem(payload).unwrap();
    }
    resetForm();
  };

  return (
    <section className="admin-page">
      <div className="admin-page-heading">
        <div>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        <Button variant="secondary" onClick={resetForm}>
          Добавить
        </Button>
      </div>

      <Card className="admin-filter-card">
        <label className="compact-field">
          Поиск
          <input
            value={filters.q}
            onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
            placeholder="Название, номер или адрес"
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

      <div className="admin-crud-layout">
        <Card>
          {isLoading ? <LoadingState /> : null}
          {isError ? <Alert tone="danger">Не удалось загрузить список.</Alert> : null}
          {!isLoading && !isError ? (
            <DataTable columns={preparedColumns} rows={data} emptyText={emptyText} />
          ) : null}
          {isFetching && !isLoading ? <p className="field-hint">Обновляем данные...</p> : null}
        </Card>

        <Card className="admin-form-card">
          <h2>{editingItem ? "Редактирование" : "Создание"}</h2>
          {saveError ? <Alert tone="danger">{errorMessage(saveError)}</Alert> : null}
          <form className="admin-form" onSubmit={handleSubmit}>
            {fields.map((field) => (
              <label key={field.name} className="form-field">
                {field.label}
                {field.type === "select" ? (
                  <select
                    value={form[field.name] ?? ""}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, [field.name]: event.target.value }))
                    }
                    required={field.required}
                  >
                    {field.options.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input
                    type={field.type || "text"}
                    step={field.step}
                    min={field.min}
                    value={form[field.name] ?? ""}
                    onChange={(event) =>
                      setForm((current) => ({ ...current, [field.name]: event.target.value }))
                    }
                    required={field.required}
                  />
                )}
              </label>
            ))}
            <div className="form-actions">
              <button type="submit" disabled={isSaving}>
                {isSaving ? "Сохраняем..." : "Сохранить"}
              </button>
              {editingItem ? (
                <button type="button" className="button-secondary" onClick={resetForm}>
                  Отменить
                </button>
              ) : null}
            </div>
          </form>
        </Card>
      </div>
    </section>
  );
}
