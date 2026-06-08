import { baseApi } from "./baseApi.js";
import { clearCredentials, setAccessToken, setCredentials } from "../features/auth/authSlice.js";

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => ({
        url: "auth/token/",
        method: "POST",
        body: credentials
      }),
      async onQueryStarted(_credentials, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        sessionStorage.setItem("ecologist.refreshToken", data.refresh);
        dispatch(setCredentials({ accessToken: data.access, refreshToken: data.refresh }));
      }
    }),
    currentUser: builder.query({
      query: () => "auth/me/",
      providesTags: ["Auth"]
    }),
    registerManager: builder.mutation({
      query: (payload) => ({
        url: "auth/register/",
        method: "POST",
        body: payload,
        timeout: 15000
      })
    }),
    refreshAccess: builder.mutation({
      query: (refreshToken) => ({
        url: "auth/token/refresh/",
        method: "POST",
        body: { refresh: refreshToken }
      }),
      async onQueryStarted(refreshToken, { dispatch, queryFulfilled }) {
        const { data } = await queryFulfilled;
        if (data.refresh) {
          dispatch(setCredentials({ accessToken: data.access, refreshToken: data.refresh }));
        } else {
          sessionStorage.setItem("ecologist.refreshToken", refreshToken);
          dispatch(setAccessToken(data.access));
        }
      }
    }),
    logout: builder.mutation({
      queryFn: (_arg, { dispatch }) => {
        sessionStorage.removeItem("ecologist.refreshToken");
        dispatch(clearCredentials());
        dispatch(baseApi.util.resetApiState());
        return { data: null };
      }
    })
  })
});

export const {
  useCurrentUserQuery,
  useLoginMutation,
  useLogoutMutation,
  useRegisterManagerMutation,
  useRefreshAccessMutation
} = authApi;
