import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import type { Session } from "@supabase/supabase-js";

import { PortalShell } from "@/shared/components/PortalShell";
import { AdminInternalNav } from "@/admin/components/AdminInternalNav";
import { formatApiError, internalAuthProbe } from "@/shared/lib/api";
import { hasSupabaseAuthConfig } from "@/shared/lib/env";
import {
  getCurrentSession,
  onAuthStateChange,
  signOut,
} from "@/shared/lib/supabase";

type Props = {
  children: ReactNode;
};

export function AdminRouteGuard({ children }: Props) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [adminOk, setAdminOk] = useState<boolean | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!hasSupabaseAuthConfig()) {
      setLoading(false);
      return;
    }
    let active = true;
    getCurrentSession().then((s) => {
      if (active) setSession(s);
      setLoading(false);
    });
    const unsubscribe = onAuthStateChange((s) => {
      setSession(s);
      setAdminOk(null);
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!session) {
      setAdminOk(null);
      return;
    }
    let cancelled = false;
    internalAuthProbe()
      .then(() => {
        if (!cancelled) setAdminOk(true);
      })
      .catch((err) => {
        if (!cancelled) {
          setAdminOk(false);
          setError(formatApiError(err));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [session]);

  async function handleSignOut() {
    await signOut();
    setSession(null);
    setAdminOk(null);
    setError("");
  }

  if (!hasSupabaseAuthConfig()) {
    return (
      <div className="mx-auto max-w-lg p-8">
        <p className="text-red-700">
          Supabase is not configured. Copy <code>.env.example</code> to <code>.env</code> and set{" "}
          <code>VITE_SUPABASE_URL</code> and <code>VITE_SUPABASE_PUBLISHABLE_KEY</code>.
        </p>
      </div>
    );
  }

  if (loading) {
    return <p className="p-8 text-slate-600">Loading session…</p>;
  }

  if (!session) {
    return <Navigate to="/access" replace />;
  }

  if (adminOk === null) {
    return <p className="p-8 text-slate-600">Verifying internal admin access…</p>;
  }

  if (!adminOk) {
    return <Navigate to="/access/denied" replace state={{ message: error }} />;
  }

  return (
    <PortalShell email={session.user.email} onSignOut={handleSignOut}>
      <AdminInternalNav />
      {children}
    </PortalShell>
  );
}
