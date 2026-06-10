import { useEffect, useMemo, useRef, useState } from "react";

import {
  useAvatarBlobQuery,
  useDeleteAvatarMutation,
  useProfileQuery,
  useUpdateProfileMutation,
  useUploadAvatarMutation
} from "../api/profileApi.js";
import Alert from "../components/ui/Alert.jsx";
import Button from "../components/ui/Button.jsx";
import Card from "../components/ui/Card.jsx";
import FormField from "../components/ui/FormField.jsx";
import LoadingState from "../components/ui/LoadingState.jsx";
import PageShell from "../components/ui/PageShell.jsx";

const AVATAR_MAX_SIZE_BYTES = 5 * 1024 * 1024;
const AVATAR_ALLOWED_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);

function initialForm(profile) {
  return {
    first_name: profile?.first_name || "",
    last_name: profile?.last_name || "",
    middle_name: profile?.middle_name || "",
    email: profile?.email || "",
    phone: profile?.phone || ""
  };
}

function fieldError(error, field) {
  const value = error?.data?.[field];
  if (Array.isArray(value)) {
    return value[0];
  }
  return value || "";
}

function profileRoleLabel(role) {
  return role === "admin" ? "Администратор" : "Менеджер";
}

export default function ProfilePage() {
  const fileInputRef = useRef(null);
  const [isEditing, setIsEditing] = useState(false);
  const [form, setForm] = useState(initialForm(null));
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const { data: profile, error: profileError, isLoading } = useProfileQuery();
  const { data: avatarBlob } = useAvatarBlobQuery(undefined, {
    skip: !profile?.avatar_exists
  });
  const [updateProfile, { error: updateError, isLoading: isSaving }] = useUpdateProfileMutation();
  const [uploadAvatar, { isLoading: isUploading }] = useUploadAvatarMutation();
  const [deleteAvatar, { isLoading: isDeleting }] = useDeleteAvatarMutation();

  useEffect(() => {
    if (profile) {
      setForm(initialForm(profile));
    }
  }, [profile]);

  useEffect(() => {
    if (!avatarBlob) {
      setAvatarUrl("");
      return undefined;
    }
    const objectUrl = URL.createObjectURL(avatarBlob);
    setAvatarUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [avatarBlob]);

  const avatarSrc = avatarUrl || "/static/img/profile-avatar-placeholder.png";
  const isBusy = isSaving || isUploading || isDeleting;
  const avatarButtonLabel = useMemo(() => {
    if (isUploading) {
      return "Загружаем...";
    }
    return profile?.avatar_exists ? "Изменить фото" : "Загрузить фото";
  }, [isUploading, profile?.avatar_exists]);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleEdit = () => {
    setMessage("");
    setErrorMessage("");
    setForm(initialForm(profile));
    setIsEditing(true);
  };

  const handleCancel = () => {
    setMessage("");
    setErrorMessage("");
    setForm(initialForm(profile));
    setIsEditing(false);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    setErrorMessage("");
    try {
      await updateProfile(form).unwrap();
      setIsEditing(false);
      setMessage("Профиль обновлен.");
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось сохранить профиль.");
    }
  };

  const handleAvatarSelect = async (event) => {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }

    setMessage("");
    setErrorMessage("");
    if (file.size > AVATAR_MAX_SIZE_BYTES) {
      setErrorMessage("Файл слишком большой.");
      return;
    }
    if (!AVATAR_ALLOWED_TYPES.has(file.type)) {
      setErrorMessage("Недопустимый формат файла.");
      return;
    }

    try {
      await uploadAvatar(file).unwrap();
      setMessage("Фото профиля обновлено.");
    } catch (error) {
      setErrorMessage(error?.data?.avatar?.[0] || error?.data?.detail || "Не удалось загрузить фото.");
    }
  };

  const handleDeleteAvatar = async () => {
    setMessage("");
    setErrorMessage("");
    try {
      await deleteAvatar().unwrap();
      setMessage("Фото профиля удалено.");
    } catch (error) {
      setErrorMessage(error?.data?.detail || "Не удалось удалить фото профиля.");
    }
  };

  if (isLoading) {
    return <LoadingState text="Загрузка профиля..." />;
  }

  if (profileError || !profile) {
    return <Alert tone="danger">Не удалось загрузить профиль.</Alert>;
  }

  const displayName =
    [profile.last_name, profile.first_name].filter(Boolean).join(" ") || profile.username;

  return (
    <PageShell
      title="Профиль"
      subtitle="Управляйте своими персональными данными и настройками аккаунта."
      className="profile-panel"
      variant="wide"
      actions={
        isEditing ? (
          <Button variant="secondary" onClick={handleCancel}>
            К профилю
          </Button>
        ) : (
          <Button variant="secondary" onClick={handleEdit} className="profile-edit-button">
            Редактировать профиль
          </Button>
        )
      }
    >
      {message ? <Alert tone="success">{message}</Alert> : null}
      {errorMessage ? <Alert tone="danger">{errorMessage}</Alert> : null}

      <section className="profile-layout">
        <Card className="profile-avatar-card">
          <div className="profile-avatar-frame">
            <img className="profile-avatar" src={avatarSrc} alt="Фото профиля" />
          </div>
          <h2>{displayName}</h2>
          <span className="profile-role-badge">{profileRoleLabel(profile.role)}</span>

          <div className="profile-avatar-note">
            <img src="/static/img/eco-leaf-icon.png" alt="" aria-hidden="true" />
            <p>Вы можете добавить фотографию профиля, чтобы персонализировать свой аккаунт.</p>
          </div>

          {isEditing ? (
            <div className="profile-avatar-edit">
              <input
                ref={fileInputRef}
                className="visually-hidden"
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleAvatarSelect}
              />
              <Button
                className="profile-avatar-upload-button"
                disabled={isBusy}
                onClick={() => fileInputRef.current?.click()}
              >
                {avatarButtonLabel}
              </Button>
              {profile.avatar_exists ? (
                <Button
                  variant="danger"
                  className="profile-avatar-delete-button"
                  disabled={isBusy}
                  onClick={handleDeleteAvatar}
                >
                  {isDeleting ? "Удаляем..." : "Удалить фото"}
                </Button>
              ) : null}
              <p className="profile-upload-hint">
                Рекомендуемый формат: JPG, PNG или WEBP. Максимальный размер файла: 5 МБ.
              </p>
            </div>
          ) : null}
        </Card>

        <Card className="profile-data-card">
          <div className="profile-data-heading">
            <h2>Личные данные</h2>
          </div>

          {isEditing ? (
            <form className="profile-data-form" onSubmit={handleSubmit}>
              <FormField
                label="Фамилия"
                name="last_name"
                value={form.last_name}
                onChange={updateField}
                error={fieldError(updateError, "last_name")}
              />
              <FormField
                label="Имя"
                name="first_name"
                value={form.first_name}
                onChange={updateField}
                error={fieldError(updateError, "first_name")}
              />
              <FormField
                label="Отчество"
                name="middle_name"
                value={form.middle_name}
                onChange={updateField}
                error={fieldError(updateError, "middle_name")}
              />
              <FormField
                label="Email"
                name="email"
                type="email"
                value={form.email}
                onChange={updateField}
                error={fieldError(updateError, "email")}
              />
              <FormField
                label="Телефон"
                name="phone"
                value={form.phone}
                onChange={updateField}
                error={fieldError(updateError, "phone")}
              />
              <div className="profile-privacy-note">
                <span className="profile-shield-icon" aria-hidden="true">✓</span>
                <span>Ваши данные используются для работы в системе и не передаются третьим лицам.</span>
              </div>
              <div className="profile-save-actions">
                <Button type="submit" disabled={isSaving}>
                  {isSaving ? "Сохраняем..." : "Сохранить"}
                </Button>
                <Button variant="secondary" disabled={isSaving} onClick={handleCancel}>
                  Отмена
                </Button>
              </div>
            </form>
          ) : (
            <>
              <dl className="profile-field-grid">
                <div>
                  <dt>Имя пользователя</dt>
                  <dd>{profile.username || "Не указано"}</dd>
                </div>
                <div>
                  <dt>Фамилия</dt>
                  <dd>{profile.last_name || "Не указано"}</dd>
                </div>
                <div>
                  <dt>Имя</dt>
                  <dd>{profile.first_name || "Не указано"}</dd>
                </div>
                <div>
                  <dt>Отчество</dt>
                  <dd>{profile.middle_name || "Не указано"}</dd>
                </div>
                <div>
                  <dt>Email</dt>
                  <dd>{profile.email || "Не указано"}</dd>
                </div>
                <div>
                  <dt>Телефон</dt>
                  <dd>{profile.phone || "Не указано"}</dd>
                </div>
                <div>
                  <dt>Роль</dt>
                  <dd>{profileRoleLabel(profile.role)}</dd>
                </div>
              </dl>
              <div className="profile-privacy-note">
                <span className="profile-shield-icon" aria-hidden="true">✓</span>
                <span>Ваши данные используются для работы в системе и не передаются третьим лицам.</span>
              </div>
            </>
          )}
        </Card>
      </section>
    </PageShell>
  );
}
