import { baseApi } from "./baseApi.js";

function queryString(params = {}) {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      searchParams.set(key, value);
    }
  });
  const value = searchParams.toString();
  return value ? `?${value}` : "";
}

function filenameFromDisposition(disposition, fallback) {
  if (!disposition) {
    return fallback;
  }
  const match = disposition.match(/filename="?([^"]+)"?/i);
  return match?.[1] || fallback;
}

function downloadPayload(blob, meta, fallback) {
  return {
    filename: filenameFromDisposition(meta?.response?.headers.get("content-disposition"), fallback),
    url: URL.createObjectURL(blob)
  };
}

function listTags(result, type) {
  return result
    ? [...result.map((item) => ({ type, id: item.id })), { type, id: "LIST" }]
    : [{ type, id: "LIST" }];
}

export const adminApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    adminDashboard: builder.query({
      query: () => "admin/dashboard/",
      providesTags: ["AdminDashboard"]
    }),
    downloadAdminDashboardXlsx: builder.mutation({
      query: () => ({
        url: "admin/dashboard/export-xlsx/",
        responseHandler: (response) => response.blob()
      }),
      transformResponse: (blob, meta) => downloadPayload(blob, meta, "company_dashboard.xlsx")
    }),
    archiveAdminDashboardXlsx: builder.mutation({
      query: () => ({
        url: "admin/dashboard/export-xlsx/archive/",
        method: "POST"
      }),
      invalidatesTags: ["Archive"]
    }),
    adminUsers: builder.query({
      query: (params = {}) => `admin/users/${queryString(params)}`,
      providesTags: (result) => listTags(result, "AdminUsers")
    }),
    updateAdminUser: builder.mutation({
      query: ({ id, ...payload }) => ({
        url: `admin/users/${id}/`,
        method: "PATCH",
        body: payload
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "AdminUsers", id },
        { type: "AdminUsers", id: "LIST" },
        "AdminDashboard"
      ]
    }),
    adminTransports: builder.query({
      query: (params = {}) => `admin/transports/${queryString(params)}`,
      providesTags: (result) => listTags(result, "AdminTransports")
    }),
    createAdminTransport: builder.mutation({
      query: (payload) => ({
        url: "admin/transports/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: [{ type: "AdminTransports", id: "LIST" }, "AdminDashboard", "References"]
    }),
    updateAdminTransport: builder.mutation({
      query: ({ id, ...payload }) => ({
        url: `admin/transports/${id}/`,
        method: "PATCH",
        body: payload
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "AdminTransports", id },
        { type: "AdminTransports", id: "LIST" },
        "AdminDashboard",
        "References"
      ]
    }),
    adminLocations: builder.query({
      query: (params = {}) => `admin/locations/${queryString(params)}`,
      providesTags: (result) => listTags(result, "AdminLocations")
    }),
    createAdminLocation: builder.mutation({
      query: (payload) => ({
        url: "admin/locations/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: [{ type: "AdminLocations", id: "LIST" }, "References"]
    }),
    updateAdminLocation: builder.mutation({
      query: ({ id, ...payload }) => ({
        url: `admin/locations/${id}/`,
        method: "PATCH",
        body: payload
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "AdminLocations", id },
        { type: "AdminLocations", id: "LIST" },
        "References"
      ]
    }),
    adminEcoStandards: builder.query({
      query: (params = {}) => `admin/eco-standards/${queryString(params)}`,
      providesTags: (result) => listTags(result, "AdminEcoStandards")
    }),
    createAdminEcoStandard: builder.mutation({
      query: (payload) => ({
        url: "admin/eco-standards/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: [
        { type: "AdminEcoStandards", id: "LIST" },
        { type: "AdminTransports", id: "LIST" },
        "References"
      ]
    }),
    updateAdminEcoStandard: builder.mutation({
      query: ({ id, ...payload }) => ({
        url: `admin/eco-standards/${id}/`,
        method: "PATCH",
        body: payload
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "AdminEcoStandards", id },
        { type: "AdminEcoStandards", id: "LIST" },
        { type: "AdminTransports", id: "LIST" },
        "References"
      ]
    }),
    adminCalculationSettings: builder.query({
      query: () => "admin/calculation-settings/",
      providesTags: ["AdminSettings"]
    }),
    createAdminCalculationSettings: builder.mutation({
      query: (payload) => ({
        url: "admin/calculation-settings/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: ["AdminSettings"]
    })
  })
});

export const {
  useAdminCalculationSettingsQuery,
  useAdminDashboardQuery,
  useAdminEcoStandardsQuery,
  useAdminLocationsQuery,
  useAdminTransportsQuery,
  useAdminUsersQuery,
  useArchiveAdminDashboardXlsxMutation,
  useCreateAdminCalculationSettingsMutation,
  useCreateAdminEcoStandardMutation,
  useCreateAdminLocationMutation,
  useCreateAdminTransportMutation,
  useDownloadAdminDashboardXlsxMutation,
  useUpdateAdminEcoStandardMutation,
  useUpdateAdminLocationMutation,
  useUpdateAdminTransportMutation,
  useUpdateAdminUserMutation
} = adminApi;
