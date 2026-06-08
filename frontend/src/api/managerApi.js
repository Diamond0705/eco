import { baseApi } from "./baseApi.js";

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
  useCancelOrderMutation,
  useCreateOrderMutation,
  useLocationsQuery,
  useManagerDashboardQuery,
  useOrderQuery,
  useOrdersQuery,
  useTransportsQuery
} = managerApi;
