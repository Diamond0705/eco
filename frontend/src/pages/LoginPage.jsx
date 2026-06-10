import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { useCurrentUserQuery, useLoginMutation } from "../api/authApi.js";
import {
  selectIsAuthenticated,
  setCurrentUser
} from "../features/auth/authSlice.js";
import AuthLayout from "../layouts/AuthLayout.jsx";

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
      <AuthLayout pageClassName="login-page">
        <section className="login-card auth-status-card">
          <p>Загружаем профиль...</p>
        </section>
      </AuthLayout>
    );
  }

  if (isAuthenticated && user) {
    return <Navigate to={from || (user.is_admin ? "/admin/dashboard" : "/dashboard")} replace />;
  }

  return (
    <AuthLayout pageClassName="login-page">
      <section className="login-card">
        <div className="login-brand">
          <img
            className="login-brand-mark"
            src="/static/img/ecologist-truck-mark.png"
            alt=""
          />
          <span className="login-brand-name">EcoLogist</span>
          <span className="login-brand-subtitle">Система планирования грузоперевозок</span>
        </div>

        <h1>Вход</h1>
        <p className="muted">Введите никнейм или email и пароль</p>

        <form className="login-form" onSubmit={handleSubmit}>
          <label className="form-row">
            <span>Никнейм или email</span>
            <input
              autoComplete="username"
              placeholder="Имя пользователя или email"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label className="form-row">
            <span>Пароль</span>
            <input
              autoComplete="current-password"
              placeholder="Пароль"
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

        <p className="form-note">
          Нет учетной записи? <Link to="/register">Зарегистрироваться</Link>
        </p>
      </section>
    </AuthLayout>
  );
}
