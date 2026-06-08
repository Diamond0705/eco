import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { useCurrentUserQuery, useLoginMutation } from "../api/authApi.js";
import {
  selectIsAuthenticated,
  setCurrentUser
} from "../features/auth/authSlice.js";

export default function LoginPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [login, { isLoading, error }] = useLoginMutation();
  const { data: user, isFetching: isUserLoading } = useCurrentUserQuery(undefined, {
    skip: !isAuthenticated
  });
  const from = location.state?.from?.pathname;

  useEffect(() => {
    if (user) {
      dispatch(setCurrentUser(user));
      navigate(from || (user.is_admin ? "/admin/dashboard" : "/dashboard"), { replace: true });
    }
  }, [dispatch, from, navigate, user]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await login({ username, password }).unwrap();
    } catch {
      // RTK Query exposes the error state for the form message.
    }
  };

  if (isAuthenticated && isUserLoading) {
    return (
      <main className="login-page">
        <section className="login-card">
          <p>Загружаем профиль...</p>
        </section>
      </main>
    );
  }

  if (isAuthenticated && user) {
    return <Navigate to={from || (user.is_admin ? "/admin/dashboard" : "/dashboard")} replace />;
  }

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-brand">
          <img src="/static/img/ecologist-truck-mark.png" alt="" />
          <div>
            <p className="eyebrow">EcoLogist SPA</p>
            <h1>Вход в систему</h1>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            Логин
            <input
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label>
            Пароль
            <input
              autoComplete="current-password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error ? <p className="form-error">Не удалось войти. Проверьте логин и пароль.</p> : null}
          <button type="submit" disabled={isLoading}>
            {isLoading ? "Входим..." : "Войти"}
          </button>
        </form>
      </section>
    </main>
  );
}
