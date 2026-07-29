import { createBrowserRouter, Navigate } from "react-router-dom";
import Layout from "../layouts/Layout";
import ProfilePage from "../pages/profile/ProfilePage";
import NotFoundPage from "../pages/NotFound/NotFoundPage";
import LoginPage from "../pages/auth/LoginPage";
import RegisterPage from "../pages/auth/RegisterPage";
import Dashboard from "../pages/Dashboard";
import { useAuthStore } from "../stores/authStore";
import ObjectsPage from "../pages/objects/ObjectsPage";
import ObjectDetailPage from "../pages/objects/ObjectDetailPage";
import SuppliersPage from "../pages/suppliers/SuppliersPage";
import SupplierDetailPage from "../pages/suppliers/SupplierDetailPage";
import WarehousesPage from "../pages/warehouses/WarehousesPage";
import WarehouseDetailPage from "../pages/warehouses/WarehouseDetailPage";
import ShartnomalarPage from "../pages/shartnomalar/ShartnomalarPage";
import ShartnomaDetailPage from "../pages/shartnomalar/ShartnomaDetailPage";
import InventoryPage from "../pages/inventory/InventoryPage";
import InventoryDetailPage from "../pages/inventory/InventoryDetailPage";
import MaterialsPage from "../pages/materials/MaterialsPage";
import MaterialDetailPage from "../pages/materials/MaterialDetailPage";
import NotificationsPage from "../pages/notifications/NotificationsPage";
import PurchasesPage from "../pages/purchases/PurchasesPage";
import PurchaseOrderDetailPage from "../pages/purchases/PurchaseOrderDetailPage";
import TicketsPage from "../pages/tickets/TicketsPage";
import TicketDetailPage from "../pages/tickets/TicketDetailPage";
import InvoicesPage from "../pages/invoices/InvoicesPage";
import InvoiceDetailPage from "../pages/invoices/InvoiceDetailPage";
import UsersPage from "../pages/users/UsersPage";
import UserDetailPage from "../pages/users/UserDetailPage";
import DocumentsPage from "../pages/documents/DocumentsPage";
import DocumentDetailPage from "../pages/documents/DocumentDetailPage";
import ProductionRequestsPage from "../pages/production-requests/ProductionRequestsPage";
import ProductionRequestDetailPage from "../pages/production-requests/ProductionRequestDetailPage";
import AuditLogsPage from "../pages/audit-logs/AuditLogsPage";
import SettingsPage from "../pages/settings/SettingsPage";
import AddressesPage from "../pages/addresses/AddressesPage";
import AddressDetailPage from "../pages/addresses/AddressDetailPage";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const accessToken = useAuthStore((state) => state.accessToken);
  console.log(accessToken);

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

const router = createBrowserRouter([
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "/profile",
        element: <ProfilePage />,
      },
      {
        path: "/settings",
        element: <SettingsPage />,
      },
      {
        path: "/objects",
        element: <ObjectsPage />,
      },
      {
        path: "/objects/:id",
        element: <ObjectDetailPage />,
      },
      {
        path: "/suppliers",
        element: <SuppliersPage />,
      },
      {
        path: "/suppliers/:id",
        element: <SupplierDetailPage />,
      },
      {
        path: "/warehouse",
        element: <WarehousesPage />,
      },
      {
        path: "/warehouse/:id",
        element: <WarehouseDetailPage />,
      },
      {
        path: "/inventory",
        element: <InventoryPage />,
      },
      {
        path: "/inventory/:id",
        element: <InventoryDetailPage />,
      },
      {
        path: "/contracts",
        element: <ShartnomalarPage />,
      },
      {
        path: "/contracts/:id",
        element: <ShartnomaDetailPage />,
      },
      {
        path: "/materials",
        element: <MaterialsPage />,
      },
      {
        path: "/materials/:id",
        element: <MaterialDetailPage />,
      },
      {
        path: "/notifications",
        element: <NotificationsPage />,
      },
      {
        path: "/purchases",
        element: <PurchasesPage />,
      },
      {
        path: "/purchases/:id",
        element: <PurchaseOrderDetailPage />,
      },
      {
        path: "/tickets",
        element: <TicketsPage />,
      },
      {
        path: "/tickets/:id",
        element: <TicketDetailPage />,
      },
      {
        path: "/invoices",
        element: <InvoicesPage />,
      },
      {
        path: "/invoices/:id",
        element: <InvoiceDetailPage />,
      },
      {
        path: "/users",
        element: <UsersPage />,
      },
      {
        path: "/users/:id",
        element: <UserDetailPage />,
      },
      {
        path: "/documents",
        element: <DocumentsPage />,
      },
      {
        path: "/documents/:id",
        element: <DocumentDetailPage />,
      },
      {
        path: "/production-requests",
        element: <ProductionRequestsPage />,
      },
      {
        path: "/production-requests/:id",
        element: <ProductionRequestDetailPage />,
      },
      {
        path: "/audit-logs",
        element: <AuditLogsPage />,
      },
      {
        path: "/addresses",
        element: <AddressesPage />,
      },
      {
        path: "/addresses/:id",
        element: <AddressDetailPage />,
      },

      {
        path: "*",
        element: <NotFoundPage />,
      },
    ],
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/register",
    element: <RegisterPage />,
  },
]);

export default router;
