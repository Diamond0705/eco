import {
  useAdminLocationsQuery,
  useCreateAdminLocationMutation,
  useUpdateAdminLocationMutation
} from "../../api/adminApi.js";
import Badge from "../../components/ui/Badge.jsx";
import AdminReferencePage from "./AdminReferencePage.jsx";

const defaultValues = {
  name: "",
  address: "",
  latitude: "",
  longitude: "",
  is_active: "1"
};

function normalizePayload(form) {
  return {
    ...form,
    is_active: form.is_active === "1"
  };
}

export default function AdminLocationsPage() {
  return (
    <AdminReferencePage
      title="Локации"
      description="Учебные точки отправления и доставки с координатами для построения маршрутов."
      emptyText="Локации не найдены."
      useListQuery={useAdminLocationsQuery}
      useCreateMutation={useCreateAdminLocationMutation}
      useUpdateMutation={useUpdateAdminLocationMutation}
      defaultValues={defaultValues}
      normalizePayload={normalizePayload}
      fields={[
        { name: "name", label: "Название", required: true },
        { name: "address", label: "Адрес" },
        {
          name: "latitude",
          label: "Широта",
          type: "number",
          step: "0.000001",
          min: "-90",
          required: true
        },
        {
          name: "longitude",
          label: "Долгота",
          type: "number",
          step: "0.000001",
          min: "-180",
          required: true
        },
        {
          name: "is_active",
          label: "Активность",
          type: "select",
          options: [
            { value: "1", label: "Активна" },
            { value: "0", label: "Неактивна" }
          ]
        }
      ]}
      columns={[
        { key: "name", label: "Название" },
        { key: "address", label: "Адрес" },
        { key: "latitude", label: "Широта" },
        { key: "longitude", label: "Долгота" },
        {
          key: "is_active",
          label: "Статус",
          render: (row) => (
            <Badge tone={row.is_active ? "success" : "neutral"}>
              {row.is_active ? "Активна" : "Неактивна"}
            </Badge>
          )
        }
      ]}
    />
  );
}
