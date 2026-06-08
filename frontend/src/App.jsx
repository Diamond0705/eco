import { Navigate, Route, Routes } from "react-router-dom";
import { useSelector } from "react-redux";

import AdminLayout from "./layouts/AdminLayout.jsx";
import AppLayout from "./layouts/AppLayout.jsx";
import ArchivePage from "./pages/ArchivePage.jsx";
import AdminCalculationSettingsPage from "./pages/admin/AdminCalculationSettingsPage.jsx";
import AdminDashboardPage from "./pages/admin/AdminDashboardPage.jsx";
import AdminEcoStandardsPage from "./pages/admin/AdminEcoStandardsPage.jsx";
import AdminLocationsPage from "./pages/admin/AdminLocationsPage.jsx";
import AdminTransportsPage from "./pages/admin/AdminTransportsPage.jsx";
import AdminUsersPage from "./pages/admin/AdminUsersPage.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import EmissionsReportPage from "./pages/EmissionsReportPage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import ManagerAnalyticsPage from "./pages/ManagerAnalyticsPage.jsx";
import NotFoundPage from "./pages/NotFoundPage.jsx";
import OrderCreatePage from "./pages/OrderCreatePage.jsx";
import OrderDetailPage from "./pages/OrderDetailPage.jsx";
import OrdersListPage from "./pages/OrdersListPage.jsx";
import ProfilePage from "./pages/ProfilePage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import RouteComparisonPage from "./pages/RouteComparisonPage.jsx";
import TripDetailPage from "./pages/TripDetailPage.jsx";
import TripsListPage from "./pages/TripsListPage.jsx";
import { selectCurrentUser } from "./features/auth/authSlice.js";
import ProtectedRoute from "./routes/ProtectedRoute.jsx";
import RoleRoute from "./routes/RoleRoute.jsx";

function HomeRedirect() {
  const user = useSelector(selectCurrentUser);
  return <Navigate to={user?.is_admin ? "/admin/dashboard" : "/dashboard"} replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<HomeRedirect />} />
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
            path="/analytics"
            element={
              <RoleRoute allowedRoles={["manager"]}>
                <ManagerAnalyticsPage />
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
          <Route path="/profile" element={<ProfilePage />} />
        </Route>
        <Route
          element={
            <RoleRoute allowedRoles={["admin"]}>
              <AdminLayout />
            </RoleRoute>
          }
        >
          <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
          <Route path="/admin/archive" element={<ArchivePage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/transports" element={<AdminTransportsPage />} />
          <Route path="/admin/locations" element={<AdminLocationsPage />} />
          <Route path="/admin/eco-standards" element={<AdminEcoStandardsPage />} />
          <Route
            path="/admin/calculation-settings"
            element={<AdminCalculationSettingsPage />}
          />
          <Route path="/admin/profile" element={<ProfilePage />} />
        </Route>
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
