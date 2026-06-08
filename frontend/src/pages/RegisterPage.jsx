import { useState } from "react";
import { useSelector } from "react-redux";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { useRegisterManagerMutation } from "../api/authApi.js";
import { selectCurrentUser, selectIsAuthenticated } from "../features/auth/authSlice.js";
import AuthLayout from "../layouts/AuthLayout.jsx";

const initialForm = {
  username: "",
  email: "",
  first_name: "",
  last_name: "",
  middle_name: "",
  phone: "",
  password1: "",
  password2: ""
};

const fields = [
  {
    name: "username",
    label: "Уникальный никнейм",
    autoComplete: "username",
    placeholder: "ivan_petrov",
    help: "Никнейм используется для входа и должен быть уникальным."
  },
  { name: "email", label: "Email", type: "email", autoComplete: "email" },
  { name: "first_name", label: "Имя", autoComplete: "given-name" },
  { name: "last_name", label: "Фамилия", autoComplete: "family-name" },
  { name: "middle_name", label: "Отчество", autoComplete: "additional-name" },
  {
    name: "phone",
    label: "Телефон",
    autoComplete: "tel",
    placeholder: "+7 (999) 123-45-67",
    help: "Предпочтительный формат: +7 (999) 123-45-67"
  },
  {
    name: "password1",
    label: "Пароль",
    type: "password",
    autoComplete: "new-password",
    help: "Минимум 8 символов. Не используйте слишком простой пароль."
  },
  {
    name: "password2",
    label: "Подтверждение пароля",
    type: "password",
    autoComplete: "new-password",
    help: "Введите тот же пароль еще раз."
  }
];

function messagesFor(error, fieldName) {
  const data = error?.data;
  const value = data?.[fieldName];
  return normalizeMessages(value);
}

function normalizeMessages(value) {
  if (Array.isArray(value)) {
    return value.flatMap((item) => normalizeMessages(item));
  }
  if (typeof value === "string") {
    return [value];
  }
  if (value && typeof value === "object") {
    return Object.values(value).flatMap((item) => normalizeMessages(item));
  }
  return [];
}

function statusMessage(error) {
  if (!error) {
    return "";
  }
  if (error.status === "TIMEOUT_ERROR") {
    return "Сервер не ответил. Попробуйте еще раз.";
  }
  if (error.status === "FETCH_ERROR") {
    return "Не удалось связаться с сервером. Проверьте подключение и попробуйте еще раз.";
  }
  if (error.status === "PARSING_ERROR") {
    return "Сервер вернул неожиданный ответ. Попробуйте еще раз.";
  }
  if (error.data?.detail) {
    return normalizeMessages(error.data.detail).join(" ");
  }
  return "Не удалось завершить регистрацию. Проверьте данные и попробуйте еще раз.";
}

export default function RegisterPage() {
  const navigate = useNavigate();
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const currentUser = useSelector(selectCurrentUser);
  const [form, setForm] = useState(initialForm);
  const [registerManager, { isLoading, error }] = useRegisterManagerMutation();

  if (isAuthenticated) {
    return <Navigate to={currentUser?.is_admin ? "/admin/dashboard" : "/dashboard"} replace />;
  }

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    try {
      await registerManager(form).unwrap();
      setForm(initialForm);
      navigate("/login", {
        replace: true,
        state: { message: "Регистрация завершена. Теперь войдите в систему." }
      });
    } catch {
      // Field-level messages are rendered from RTK Query error state.
    }
  };

  const nonFieldErrors = [
    ...messagesFor(error, "non_field_errors"),
    ...messagesFor(error, "__all__")
  ];
  const hasFieldErrors = fields.some((field) => messagesFor(error, field.name).length > 0);
  const generalError = error && !nonFieldErrors.length && !hasFieldErrors ? statusMessage(error) : "";

  return (
    <AuthLayout pageClassName="register-page">
      <section className="register-card">
        <div className="register-card-header">
          <h1>Регистрация менеджера</h1>
          <p className="muted">Новая учетная запись создается с ролью менеджера.</p>
        </div>

        <form className="register-form" onSubmit={handleSubmit}>
          {nonFieldErrors.length ? (
            <div className="form-error">
              {nonFieldErrors.map((message) => (
                <p key={message}>{message}</p>
              ))}
            </div>
          ) : null}
          {generalError ? <p className="form-error">{generalError}</p> : null}

          {fields.map((field) => {
            const fieldErrors = messagesFor(error, field.name);
            return (
              <label className="form-row" key={field.name}>
                <span>{field.label}</span>
                <input
                  autoComplete={field.autoComplete}
                  name={field.name}
                  onChange={handleChange}
                  placeholder={field.placeholder || ""}
                  required={["username", "email", "password1", "password2"].includes(field.name)}
                  type={field.type || "text"}
                  value={form[field.name]}
                />
                {field.help ? <span className="help-text">{field.help}</span> : null}
                {fieldErrors.length ? (
                  <span className="field-errors">
                    {fieldErrors.map((message) => (
                      <span key={message}>{message}</span>
                    ))}
                  </span>
                ) : null}
              </label>
            );
          })}

          <button type="submit" disabled={isLoading}>
            {isLoading ? "Регистрируем..." : "Зарегистрироваться"}
          </button>
        </form>

        <p className="form-note">
          Уже есть учетная запись? <Link to="/login">Войти</Link>
        </p>
      </section>
    </AuthLayout>
  );
}
