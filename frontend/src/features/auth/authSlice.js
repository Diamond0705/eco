import { createSlice } from "@reduxjs/toolkit";

const refreshToken = sessionStorage.getItem("ecologist.refreshToken");

const initialState = {
  accessToken: null,
  refreshToken,
  user: null
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials(state, action) {
      state.accessToken = action.payload.accessToken;
      state.refreshToken = action.payload.refreshToken;
    },
    setAccessToken(state, action) {
      state.accessToken = action.payload;
    },
    setCurrentUser(state, action) {
      state.user = action.payload;
    },
    clearCredentials(state) {
      state.accessToken = null;
      state.refreshToken = null;
      state.user = null;
      sessionStorage.removeItem("ecologist.refreshToken");
    }
  }
});

export const { clearCredentials, setAccessToken, setCredentials, setCurrentUser } =
  authSlice.actions;

export const selectAccessToken = (state) => state.auth.accessToken;
export const selectCurrentUser = (state) => state.auth.user;
export const selectRefreshToken = (state) => state.auth.refreshToken;
export const selectIsAuthenticated = (state) =>
  Boolean(state.auth.accessToken || state.auth.refreshToken);

export default authSlice.reducer;
