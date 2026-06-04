import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import type { Session } from "@supabase/supabase-js";

import { PortalShell } from "@/shared/components/PortalShell";
import {
  formatApiError,
  isApiRequestError,
  ownerAuthProbe,
  type OwnerAuthProbeBody,
} from "@/shared/lib/api";
import { hasSupabaseAuthConfig } from "@/shared/lib/env";
import { ownerProbeRequiresMfaOnAccess } from "@/shared/lib/portalRole";
import { getCurrentSession, onAuthStateChange, signOut } from "@/shared/lib/supabase";

type Props = {
  children: ReactNode;
};

export function OwnerRouteGuard({ children }: Props) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [probe, setProbe] = useState<OwnerAuthProbeBody | null>(null);
  const [probeStatus, setProbeStatus] = useState<200 | 403 | null>(null);
  const [probeResolved, setProbeResolved] = useState(false);
  const [error, setError] = useState<unknown>(null);

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
      setProbe(null);
      setProbeStatus(null);
      setProbeResolved(false);
    });
    return () => {
      active = false;
      unsubscribe();
    };
  }, []);

  useEffect(() => {
    if (!session) {
      setProbe(null);
      setProbeStatus(null);
      setProbeResolved(false);
      return;
    }
    let cancelled = false;
    setProbeResolved(false);
    ownerAuthProbe()
      .then((result) => {
        if (!cancelled) {
          setProbe(result.body);
          setProbeStatus(result.status);
          setProbeResolved(true);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setProbe(null);
          setProbeStatus(null);
          setError(err);
          setProbeResolved(true);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [session]);

  async function handleSignOut() {
    await signOut();
    setSession(null);
    setProbe(null);
    setProbeStatus(null);
      setError(null);
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

  if (!probeResolved) {
    if (error) {
      if (isApiRequestError(error) && error.code === "unauthorized") {
        return <Navigate to="/access?reason=session_expired" replace />;
      }
      return (
        <Navigate
          to="/access/denied"
          replace
          state={{ message: formatApiError(error) }}
        />
      );
    }
    return <p className="p-8 text-slate-600">Verifying owner portal access…</p>;
  }

  if (probeStatus === 403 || !probe?.owner_account_exists) {
    return <Navigate to="/access" replace state={{ reason: "owner_not_provisioned" }} />;
  }

  if (ownerProbeRequiresMfaOnAccess(probe)) {
    return <Navigate to="/access" replace state={{ reason: "enroll_mfa" }} />;
  }

  return (
    <PortalShell email={session.user.email} onSignOut={handleSignOut}>
      {children}
    </PortalShell>
  );
}
