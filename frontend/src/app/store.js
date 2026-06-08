import { configureStore } from "@reduxjs/toolkit";

import { baseApi } from "../api/baseApi.js";
import authReducer from "../features/auth/authSlice.js";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    [baseApi.reducerPath]: baseApi.reducer
  },
  middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(baseApi.middleware)
});
