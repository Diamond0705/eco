import { useSelector } from "react-redux";

import Card from "../components/ui/Card.jsx";
import { selectCurrentUser } from "../features/auth/authSlice.js";

export default function RoleRoute({ allowedRoles, children }) {
  const user = useSelector(selectCurrentUser);

  if (!user) {
    return null;
  }

  const hasRole = allowedRoles.includes(user.role);
  const hasAdminAccess = allowedRoles.includes("admin") && user.is_admin;

  if (!hasRole && !hasAdminAccess) {
    return (
      <main className="page-shell">
        <Card>
          <p className="eyebrow">Доступ ограничен</p>
          <h2>Этот раздел недоступен для вашей роли</h2>
          <p>Проверьте учетную запись или вернитесь в доступный раздел EcoLogist.</p>
        </Card>
      </main>
    );
  }

  return children;
}
