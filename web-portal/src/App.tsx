import { Navigate, Route, Routes } from "react-router-dom";

import { AdminRouteGuard } from "@/admin/components/AdminRouteGuard";
import { FounderVenueDetailPage } from "@/admin/pages/FounderVenueDetailPage";
import { FounderVenuesListPage } from "@/admin/pages/FounderVenuesListPage";
import { OwnerClaimDetailPage } from "@/admin/pages/OwnerClaimDetailPage";
import { OwnerClaimsListPage } from "@/admin/pages/OwnerClaimsListPage";
import { AccessDeniedPage } from "@/owner/pages/AccessDeniedPage";
import { OwnerPortalEntry } from "@/owner/pages/OwnerPortalEntry";
import { OwnerVenueBasicsPage } from "@/owner/pages/OwnerVenueBasicsPage";
import { OwnerVenueFeaturesPage } from "@/owner/pages/OwnerVenueFeaturesPage";
import { OwnerVenueHub } from "@/owner/pages/OwnerVenueHub";
import { PortalEntryPage } from "@/owner/pages/PortalEntryPage";
import { OwnerRouteGuard } from "@/owner/components/OwnerRouteGuard";
import { RootRedirect } from "@/shared/components/RootRedirect";

function AdminAppRoutes() {
  return (
    <Routes>
      <Route index element={<Navigate to="founder-venues" replace />} />
      <Route path="founder-venues" element={<FounderVenuesListPage />} />
      <Route path="founder-venues/:leadId" element={<FounderVenueDetailPage />} />
      <Route path="owner-claims" element={<OwnerClaimsListPage />} />
      <Route path="owner-claims/:claimRequestId" element={<OwnerClaimDetailPage />} />
      <Route path="*" element={<Navigate to="founder-venues" replace />} />
    </Routes>
  );
}

function OwnerAppRoutes() {
  return (
    <Routes>
      <Route index element={<OwnerPortalEntry />} />
      <Route path="venues/:venueId" element={<OwnerVenueHub />} />
      <Route path="venues/:venueId/basics" element={<OwnerVenueBasicsPage />} />
      <Route path="venues/:venueId/features" element={<OwnerVenueFeaturesPage />} />
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
