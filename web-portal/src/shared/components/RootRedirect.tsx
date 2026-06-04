import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { resolvePortalRole, getDefaultPathForRole } from "@/shared/lib/portalRole";
import { getCurrentSession } from "@/shared/lib/supabase";

export function RootRedirect() {
  const [target, setTarget] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const session = await getCurrentSession();
      if (!session) {
        if (!cancelled) setTarget("/access");
        return;
      }
      const role = await resolvePortalRole();
      if (!cancelled) setTarget(getDefaultPathForRole(role));
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  if (!target) {
    return <p className="p-8 text-slate-600">Loading…</p>;
  }

  return <Navigate to={target} replace />;
}
