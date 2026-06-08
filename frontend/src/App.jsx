import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import OrderCreatePage from "./pages/OrderCreatePage.jsx";
import OrderDetailPage from "./pages/OrderDetailPage.jsx";
import OrdersListPage from "./pages/OrdersListPage.jsx";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";
import RoleRoute from "./routes/RoleRoute.jsx";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <DashboardPage />
              </RoleRoute>
            }
          />
          <Route
            path="/orders"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <OrdersListPage />
              </RoleRoute>
            }
          />
          <Route
            path="/orders/create"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <OrderCreatePage />
              </RoleRoute>
            }
          />
          <Route
            path="/orders/:id"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <OrderDetailPage />
              </RoleRoute>
            }
          />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
