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

export const managerApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    managerDashboard: builder.query({
      query: () => "manager/dashboard/",
      providesTags: ["Dashboard"]
    }),
    orders: builder.query({
      query: () => "orders/",
      providesTags: (result) =>
        result
          ? [
              ...result.map((order) => ({ type: "Order", id: order.id })),
              { type: "Orders", id: "LIST" }
            ]
          : [{ type: "Orders", id: "LIST" }]
    }),
    order: builder.query({
      query: (id) => `orders/${id}/`,
      providesTags: (_result, _error, id) => [{ type: "Order", id }]
    }),
    createOrder: builder.mutation({
      query: (payload) => ({
        url: "orders/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: [
        { type: "Orders", id: "LIST" },
        "Dashboard"
      ]
    }),
    cancelOrder: builder.mutation({
      query: (id) => ({
        url: `orders/${id}/cancel/`,
        method: "POST"
      }),
      invalidatesTags: (_result, _error, id) => [
        { type: "Order", id },
        { type: "Orders", id: "LIST" },
        "Dashboard"
      ]
    }),
    calculateRoutes: builder.mutation({
      query: ({ orderId, mode = "standard" }) => ({
        url: `orders/${orderId}/calculate-routes/`,
        method: "POST",
        body: { route_calculation_mode: mode }
      }),
      invalidatesTags: (_result, _error, { orderId }) => [
        { type: "Order", id: orderId },
        { type: "RouteOptions", id: orderId },
        { type: "Orders", id: "LIST" },
        "Dashboard"
      ]
    }),
    routeOptions: builder.query({
      query: (orderId) => `orders/${orderId}/route-options/`,
      providesTags: (_result, _error, orderId) => [{ type: "RouteOptions", id: orderId }]
    }),
    approveRoute: builder.mutation({
      query: ({ orderId, routeOptionId }) => ({
        url: `orders/${orderId}/routes/${routeOptionId}/approve/`,
        method: "POST"
      }),
      invalidatesTags: (_result, _error, { orderId }) => [
        { type: "Order", id: orderId },
        { type: "RouteOptions", id: orderId },
        { type: "Orders", id: "LIST" },
        { type: "Trips", id: "LIST" },
        "Dashboard"
      ]
    }),
    trips: builder.query({
      query: (params = {}) => `trips/${queryString(params)}`,
      providesTags: (result) =>
        result
          ? [
              ...result.map((trip) => ({ type: "Trip", id: trip.id })),
              { type: "Trips", id: "LIST" }
            ]
          : [{ type: "Trips", id: "LIST" }]
    }),
    trip: builder.query({
      query: (id) => `trips/${id}/`,
      providesTags: (_result, _error, id) => [{ type: "Trip", id }]
    }),
    startTrip: builder.mutation({
      query: ({ id, ...payload }) => ({
        url: `trips/${id}/start/`,
        method: "POST",
        body: payload
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Trip", id },
        { type: "Trips", id: "LIST" },
        "Dashboard",
        "Reports"
      ]
    }),
    deliverTrip: builder.mutation({
      query: ({ id, ...payload }) => ({
        url: `trips/${id}/deliver/`,
        method: "POST",
        body: payload
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Trip", id },
        { type: "Trips", id: "LIST" },
        "Dashboard",
        "Reports"
      ]
    }),
    emissionsReport: builder.query({
      query: (params = {}) => `reports/emissions/${queryString(params)}`,
      providesTags: ["Reports"]
    }),
    downloadEmissionsPdf: builder.mutation({
      query: (params = {}) => ({
        url: `reports/emissions/pdf/${queryString(params)}`,
        responseHandler: (response) => response.blob()
      }),
      transformResponse: (blob, meta) => downloadPayload(blob, meta, "emissions_report.pdf")
    }),
    downloadEmissionsXlsx: builder.mutation({
      query: (params = {}) => ({
        url: `reports/emissions/xlsx/${queryString(params)}`,
        responseHandler: (response) => response.blob()
      }),
      transformResponse: (blob, meta) => downloadPayload(blob, meta, "emissions_report.xlsx")
    }),
    archiveEmissionsPdf: builder.mutation({
      query: (payload = {}) => ({
        url: "reports/emissions/pdf/archive/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: ["Archive"]
    }),
    archiveEmissionsXlsx: builder.mutation({
      query: (payload = {}) => ({
        url: "reports/emissions/xlsx/archive/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: ["Archive"]
    }),
    downloadTripsXlsx: builder.mutation({
      query: (params = {}) => ({
        url: `trips/export-xlsx/${queryString(params)}`,
        responseHandler: (response) => response.blob()
      }),
      transformResponse: (blob, meta) => downloadPayload(blob, meta, "trips_export.xlsx")
    }),
    archiveTripsXlsx: builder.mutation({
      query: (payload = {}) => ({
        url: "trips/export-xlsx/archive/",
        method: "POST",
        body: payload
      }),
      invalidatesTags: ["Archive"]
    }),
    downloadWaybill: builder.mutation({
      query: (id) => ({
        url: `trips/${id}/waybill/`,
        responseHandler: (response) => response.blob()
      }),
      transformResponse: (blob, meta) => downloadPayload(blob, meta, "waybill.pdf")
    }),
    archiveWaybill: builder.mutation({
      query: (id) => ({
        url: `trips/${id}/waybill/archive/`,
        method: "POST"
      }),
      invalidatesTags: (_result, _error, id) => [{ type: "Trip", id }, "Archive"]
    }),
    archiveDocuments: builder.query({
      query: (params = {}) => `reports/archive/${queryString(params)}`,
      providesTags: (result) =>
        result
          ? [
              ...result.map((document) => ({ type: "Archive", id: document.id })),
              "Archive"
            ]
          : ["Archive"]
    }),
    downloadArchiveDocument: builder.mutation({
      query: (id) => ({
        url: `reports/archive/${id}/download/`,
        responseHandler: (response) => response.blob()
      }),
      transformResponse: (blob, meta) => downloadPayload(blob, meta, "document")
    }),
    deleteArchiveDocument: builder.mutation({
      query: (id) => ({
        url: `reports/archive/${id}/`,
        method: "DELETE"
      }),
      invalidatesTags: (_result, _error, id) => [{ type: "Archive", id }, "Archive"]
    }),
    transports: builder.query({
      query: () => "transports/",
      providesTags: ["References"]
    }),
    locations: builder.query({
      query: () => "locations/",
      providesTags: ["References"]
    })
  })
});

export const {
  useArchiveDocumentsQuery,
  useArchiveEmissionsPdfMutation,
  useArchiveEmissionsXlsxMutation,
  useArchiveTripsXlsxMutation,
  useArchiveWaybillMutation,
  useApproveRouteMutation,
  useCancelOrderMutation,
  useCalculateRoutesMutation,
  useCreateOrderMutation,
  useDeleteArchiveDocumentMutation,
  useDeliverTripMutation,
  useDownloadArchiveDocumentMutation,
  useDownloadEmissionsPdfMutation,
  useDownloadEmissionsXlsxMutation,
  useDownloadTripsXlsxMutation,
  useDownloadWaybillMutation,
  useEmissionsReportQuery,
  useLocationsQuery,
  useManagerDashboardQuery,
  useOrderQuery,
  useOrdersQuery,
  useRouteOptionsQuery,
  useStartTripMutation,
  useTripQuery,
  useTripsQuery,
  useTransportsQuery
} = managerApi;
