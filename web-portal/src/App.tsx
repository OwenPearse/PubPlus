import { Navigate, Route, Routes } from "react-router-dom";

import { AdminRouteGuard } from "@/admin/components/AdminRouteGuard";
import { FounderVenueDetailPage } from "@/admin/pages/FounderVenueDetailPage";
import { FounderVenuesListPage } from "@/admin/pages/FounderVenuesListPage";
import { AccessDeniedPage } from "@/owner/pages/AccessDeniedPage";
import { OwnerHomePlaceholder } from "@/owner/pages/OwnerHomePlaceholder";
import { PortalEntryPage } from "@/owner/pages/PortalEntryPage";
import { OwnerRouteGuard } from "@/owner/components/OwnerRouteGuard";
import { RootRedirect } from "@/shared/components/RootRedirect";

function AdminAppRoutes() {
  return (
    <Routes>
      <Route index element={<Navigate to="founder-venues" replace />} />
      <Route path="founder-venues" element={<FounderVenuesListPage />} />
      <Route path="founder-venues/:leadId" element={<FounderVenueDetailPage />} />
      <Route path="*" element={<Navigate to="founder-venues" replace />} />
    </Routes>
  );
}

function OwnerAppRoutes() {
  return (
    <Routes>
      <Route index element={<OwnerHomePlaceholder />} />
      <Route path="*" element={<Navigate to="/owner" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/access" element={<PortalEntryPage />} />
      <Route path="/access/denied" element={<AccessDeniedPage />} />
      <Route
        path="/internal/*"
        element={
          <AdminRouteGuard>
            <AdminAppRoutes />
          </AdminRouteGuard>
        }
      />
      <Route
        path="/owner/*"
        element={
          <OwnerRouteGuard>
            <OwnerAppRoutes />
          </OwnerRouteGuard>
        }
      />
      <Route path="/" element={<RootRedirect />} />
      <Route path="*" element={<RootRedirect />} />
    </Routes>
  );
}
