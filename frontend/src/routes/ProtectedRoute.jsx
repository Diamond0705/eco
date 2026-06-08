import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useCurrentUserQuery } from "../api/authApi.js";
import {
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
  const shouldLoadUser = Boolean(accessToken || refreshToken);
  const { data, isError, isFetching } = useCurrentUserQuery(undefined, {
    skip: !shouldLoadUser || Boolean(currentUser)
  });

  useEffect(() => {
    if (data) {
      dispatch(setCurrentUser(data));
    }
  }, [data, dispatch]);

  if (!shouldLoadUser || isError) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!currentUser && isFetching) {
    return (
      <main className="auth-status">
        <p>Проверяем доступ...</p>
      </main>
    );
  }

  return <Outlet />;
}
