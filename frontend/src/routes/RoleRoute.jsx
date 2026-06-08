import { useSelector } from "react-redux";

import { selectCurrentUser } from "../features/auth/authSlice.js";
import Card from "../components/ui/Card.jsx";

export default function RoleRoute({ allowedRoles, children }) {
  const user = useSelector(selectCurrentUser);

  if (!user) {
    return null;
  }

  if (!allowedRoles.includes(user.role)) {
    return (
      <main className="page-shell">
        <Card>
          <p className="eyebrow">Доступ ограничен</p>
          <h2>Этот раздел доступен менеджеру</h2>
          <p>
            React-страницы администратора будут добавлены позже. Пока используйте существующую
            Django-панель администратора.
          </p>
        </Card>
      </main>
    );
  }

  return children;
}
