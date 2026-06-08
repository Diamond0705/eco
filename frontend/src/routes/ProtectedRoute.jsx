import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useCurrentUserQuery, useRefreshAccessMutation } from "../api/authApi.js";
import {
  clearCredentials,
  selectAccessToken,
  selectCurrentUser,
  selectRefreshToken,
  setCurrentUser
} from "../features/auth/authSlice.js";

export default function ProtectedRoute() {
  const dispatch = useDispatch();
  const location = useLocation();
  const accessToken = useSelector(selectAccessToken);
  const refreshToken = useSelector(selectRefreshToken);
  const currentUser = useSelector(selectCurrentUser);
  const [refreshAccess, { isError: isRefreshError, isLoading: isRefreshing }] =
    useRefreshAccessMutation();
  const { data, isError, isFetching } = useCurrentUserQuery(undefined, {
    skip: !accessToken || Boolean(currentUser)
  });

  useEffect(() => {
    if (accessToken || !refreshToken || isRefreshing) {
      return;
    }
    refreshAccess(refreshToken)
      .unwrap()
      .catch(() => {
        dispatch(clearCredentials());
      });
  }, [accessToken, dispatch, isRefreshing, refreshAccess, refreshToken]);

  useEffect(() => {
    if (data) {
      dispatch(setCurrentUser(data));
    }
  }, [data, dispatch]);

  if ((!accessToken && !refreshToken) || isError || isRefreshError) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!accessToken || (!currentUser && isFetching)) {
    return (
      <main className="auth-status">
        <p>Проверяем доступ...</p>
      </main>
    );
  }

  return <Outlet />;
}
