import { Navigate, Route, Routes } from "react-router-dom";

import { AuthGate } from "@/shared/components/AuthGate";
import { FounderVenueDetailPage } from "@/admin/pages/FounderVenueDetailPage";
import { FounderVenuesListPage } from "@/admin/pages/FounderVenuesListPage";

export function App() {
  return (
    <AuthGate>
      <Routes>
        <Route path="/" element={<Navigate to="/internal/founder-venues" replace />} />
        <Route path="/internal/founder-venues" element={<FounderVenuesListPage />} />
        <Route
          path="/internal/founder-venues/:leadId"
          element={<FounderVenueDetailPage />}
        />
        <Route path="*" element={<Navigate to="/internal/founder-venues" replace />} />
      </Routes>
    </AuthGate>
  );
}
