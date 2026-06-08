import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import { clearCredentials, setAccessToken } from "../features/auth/authSlice.js";

const rawBaseQuery = fetchBaseQuery({
  baseUrl: "/api/v1/",
  prepareHeaders: (headers, { getState }) => {
    const accessToken = getState().auth.accessToken;
    if (accessToken) {
      headers.set("authorization", `Bearer ${accessToken}`);
    }
    return headers;
  }
});

const refreshBaseQuery = fetchBaseQuery({
  baseUrl: "/api/v1/"
});

const baseQueryWithRefresh = async (args, api, extraOptions) => {
  let result = await rawBaseQuery(args, api, extraOptions);

  if (result.error?.status !== 401) {
    return result;
  }

  const refreshToken = sessionStorage.getItem("ecologist.refreshToken");
  if (!refreshToken) {
    api.dispatch(clearCredentials());
    return result;
  }

  const refreshResult = await refreshBaseQuery(
    {
      url: "auth/token/refresh/",
      method: "POST",
      body: { refresh: refreshToken }
    },
    api,
    extraOptions
  );

  if (refreshResult.data?.access) {
    api.dispatch(setAccessToken(refreshResult.data.access));
    result = await rawBaseQuery(args, api, extraOptions);
  } else {
    api.dispatch(clearCredentials());
  }

  return result;
};

export const baseApi = createApi({
  reducerPath: "baseApi",
  baseQuery: baseQueryWithRefresh,
  tagTypes: [
    "Auth",
    "Dashboard",
    "Orders",
    "Order",
    "RouteOptions",
    "References",
    "Trips",
    "Trip",
    "Reports",
    "Archive"
  ],
  endpoints: () => ({})
});
