import {
  useAdminEcoStandardsQuery,
  useCreateAdminEcoStandardMutation,
  useUpdateAdminEcoStandardMutation
} from "../../api/adminApi.js";
import Badge from "../../components/ui/Badge.jsx";
import AdminReferencePage from "./AdminReferencePage.jsx";

const defaultValues = {
  name: "",
  nox_limit_g_per_kwh: "",
  pm_limit_mg_per_kwh: "",
  is_active: "1"
};

function normalizePayload(form) {
  return {
    ...form,
    is_active: form.is_active === "1"
  };
}

export default function AdminEcoStandardsPage() {
  return (
    <AdminReferencePage
      title="Экостандарты"
      description="Классы экологичности транспорта и предельные значения NOx/PM для расчетов."
      emptyText="Экостандарты не найдены."
      useListQuery={useAdminEcoStandardsQuery}
      useCreateMutation={useCreateAdminEcoStandardMutation}
      useUpdateMutation={useUpdateAdminEcoStandardMutation}
      defaultValues={defaultValues}
      normalizePayload={normalizePayload}
      fields={[
        { name: "name", label: "Название", required: true },
        {
          name: "nox_limit_g_per_kwh",
          label: "NOx, г/кВт·ч",
          type: "number",
          step: "0.01",
          min: "0.01",
          required: true
        },
        {
          name: "pm_limit_mg_per_kwh",
          label: "PM, мг/кВт·ч",
          type: "number",
          step: "0.01",
          min: "0.01",
          required: true
        },
        {
          name: "is_active",
          label: "Активность",
          type: "select",
          options: [
            { value: "1", label: "Активен" },
            { value: "0", label: "Неактивен" }
          ]
        }
      ]}
      columns={[
        { key: "name", label: "Название" },
        { key: "nox_limit_g_per_kwh", label: "NOx, г/кВт·ч" },
        { key: "pm_limit_mg_per_kwh", label: "PM, мг/кВт·ч" },
        {
          key: "is_active",
          label: "Статус",
          render: (row) => (
            <Badge tone={row.is_active ? "success" : "neutral"}>
              {row.is_active ? "Активен" : "Неактивен"}
            </Badge>
          )
        }
      ]}
    />
  );
}
