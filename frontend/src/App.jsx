import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./layouts/AppLayout.jsx";
import ArchivePage from "./pages/ArchivePage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import EmissionsReportPage from "./pages/EmissionsReportPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import OrderCreatePage from "./pages/OrderCreatePage.jsx";
import OrderDetailPage from "./pages/OrderDetailPage.jsx";
import OrdersListPage from "./pages/OrdersListPage.jsx";
import RouteComparisonPage from "./pages/RouteComparisonPage.jsx";
import TripDetailPage from "./pages/TripDetailPage.jsx";
import TripsListPage from "./pages/TripsListPage.jsx";
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
          <Route
            path="/orders/:id/routes"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <RouteComparisonPage />
              </RoleRoute>
            }
          />
          <Route
            path="/trips"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <TripsListPage />
              </RoleRoute>
            }
          />
          <Route
            path="/trips/:id"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <TripDetailPage />
              </RoleRoute>
            }
          />
          <Route
            path="/reports/emissions"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <EmissionsReportPage />
              </RoleRoute>
            }
          />
          <Route
            path="/archive"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <ArchivePage />
              </RoleRoute>
            }
          />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
