# Модель данных

Этот файл фиксирует целевую схему для последующих фаз. В Phase 0 реализуется только `accounts.User`.

## accounts.User

Custom user создается до первых миграций.

Поля:

- стандартные поля `AbstractUser`
- `middle_name`
- `phone`
- `role`

Роли:

- `manager`
- `admin`

`AUTH_USER_MODEL = "accounts.User"` обязателен.

## Будущие сущности

- `fleet.EcoStandard`
- `fleet.Transport`
- `fleet.EcoCalculationSettings`
- `locations.Location`
- `orders.Order`
- `orders.OrderPoint`
- `routing.RouteOption`
- `trips.Trip`
- `trips.TripStatusEvent`

Все связи с пользователями должны ссылаться на `settings.AUTH_USER_MODEL` или `get_user_model()`.
