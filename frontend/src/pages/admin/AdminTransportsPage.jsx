import {
  useAdminEcoStandardsQuery,
  useAdminTransportsQuery,
  useCreateAdminTransportMutation,
  useUpdateAdminTransportMutation
} from "../../api/adminApi.js";
import Badge from "../../components/ui/Badge.jsx";
import { formatFuel, formatWeight } from "../../utils/formatters.js";
import AdminReferencePage from "./AdminReferencePage.jsx";

const CATEGORY_OPTIONS = [
  { value: "N2", label: "N2" },
  { value: "N3", label: "N3" }
];

const FUEL_OPTIONS = [{ value: "diesel", label: "Дизель" }];

const defaultValues = {
  plate_number: "",
  model: "",
  category: "N3",
  fuel_type: "diesel",
  capacity_kg: "",
  fuel_consumption_l_per_100km: "",
  eco_standard: "",
  year: "",
  is_active: "1"
};

function normalizePayload(form) {
  return {
    ...form,
    capacity_kg: Number(form.capacity_kg),
    is_active: form.is_active === "1"
  };
}

export default function AdminTransportsPage() {
  const { data: standards = [] } = useAdminEcoStandardsQuery({ is_active: "1" });
  const standardOptions = [
    { value: "", label: "Выберите стандарт" },
    ...standards.map((standard) => ({ value: standard.id, label: standard.name }))
  ];

  return (
    <AdminReferencePage
      title="Транспорт"
      description="Справочник автомобилей, грузоподъемности, расхода топлива и экологических классов."
      emptyText="Транспорт не найден."
      useListQuery={useAdminTransportsQuery}
      useCreateMutation={useCreateAdminTransportMutation}
      useUpdateMutation={useUpdateAdminTransportMutation}
      defaultValues={defaultValues}
      normalizePayload={normalizePayload}
      fields={[
        { name: "plate_number", label: "Госномер", required: true },
        { name: "model", label: "Модель", required: true },
        { name: "category", label: "Категория", type: "select", options: CATEGORY_OPTIONS },
        { name: "fuel_type", label: "Тип топлива", type: "select", options: FUEL_OPTIONS },
        { name: "capacity_kg", label: "Грузоподъемность, кг", type: "number", min: 1, required: true },
        {
          name: "fuel_consumption_l_per_100km",
          label: "Расход топлива, л/100 км",
          type: "number",
          step: "0.01",
          min: "0.01",
          required: true
        },
        { name: "eco_standard", label: "Экостандарт", type: "select", options: standardOptions },
        { name: "year", label: "Год выпуска", type: "number", min: 1900, required: true },
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
        { key: "plate_number", label: "Госномер" },
        { key: "model", label: "Модель" },
        { key: "category_display", label: "Категория" },
        {
          key: "capacity_kg",
          label: "Груз",
          render: (row) => formatWeight(row.capacity_kg)
        },
        {
          key: "fuel_consumption_l_per_100km",
          label: "Расход",
          render: (row) => formatFuel(row.fuel_consumption_l_per_100km)
        },
        {
          key: "eco_standard",
          label: "Экостандарт",
          render: (row) => row.eco_standard_detail?.name || "—"
        },
        {
          key: "is_active",
          label: "Статус",
          render: (row) => <Badge tone={row.is_active ? "success" : "neutral"}>{row.is_active ? "Активен" : "Неактивен"}</Badge>
        }
      ]}
    />
  );
}
