import { Navigate, Route, Routes } from "react-router-dom";

import { FounderVenueDetailPage } from "@/admin/pages/FounderVenueDetailPage";
import { FounderVenuesListPage } from "@/admin/pages/FounderVenuesListPage";
import { PortalEntryPage } from "@/owner/pages/PortalEntryPage";
import { AuthGate } from "@/shared/components/AuthGate";

function AdminAppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/internal/founder-venues" replace />} />
      <Route path="/internal/founder-venues" element={<FounderVenuesListPage />} />
      <Route
        path="/internal/founder-venues/:leadId"
        element={<FounderVenueDetailPage />}
      />
      <Route path="*" element={<Navigate to="/internal/founder-venues" replace />} />
    </Routes>
  );
}

export function App() {
  return (
    <Routes>
      <Route path="/access" element={<PortalEntryPage />} />
      <Route
        path="/*"
        element={
          <AuthGate>
            <AdminAppRoutes />
          </AuthGate>
        }
      />
    </Routes>
  );
}
