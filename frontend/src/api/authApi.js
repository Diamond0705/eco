import { baseApi } from "./baseApi.js";
import { clearCredentials, setCredentials } from "../features/auth/authSlice.js";

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

export const { useLoginMutation, useCurrentUserQuery, useLogoutMutation } = authApi;
