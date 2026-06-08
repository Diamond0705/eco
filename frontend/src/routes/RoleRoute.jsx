import { useSelector } from "react-redux";
import { Navigate } from "react-router-dom";

import { selectCurrentUser } from "../features/auth/authSlice.js";

export default function RoleRoute({ allowedRoles, children }) {
  const user = useSelector(selectCurrentUser);

  if (!user) {
    return null;
  }

  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
