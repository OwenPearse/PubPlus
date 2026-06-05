import { useEffect, useRef, useState, type ReactNode } from "react";
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
import { onAuthStateChange, signOut, waitForSession } from "@/shared/lib/supabase";

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
  const sessionUserIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (!hasSupabaseAuthConfig()) {
      setLoading(false);
      return;
    }
    let active = true;
    let sawAuthEvent = false;

    const unsubscribe = onAuthStateChange((nextSession) => {
      if (!active) return;
      sawAuthEvent = true;
      const nextUserId = nextSession?.user?.id ?? null;
      if (sessionUserIdRef.current !== nextUserId) {
        sessionUserIdRef.current = nextUserId;
        setProbe(null);
        setProbeStatus(null);
        setProbeResolved(false);
        setError(null);
      }
      setSession(nextSession);
      setLoading(false);
    });

    void waitForSession().then((hydratedSession) => {
      if (!active) return;
      if (hydratedSession) {
        const hydratedUserId = hydratedSession.user?.id ?? null;
        if (sessionUserIdRef.current !== hydratedUserId) {
          sessionUserIdRef.current = hydratedUserId;
          setProbe(null);
          setProbeStatus(null);
          setProbeResolved(false);
          setError(null);
        }
        setSession(hydratedSession);
      }
      window.setTimeout(() => {
        if (active && !sawAuthEvent) setLoading(false);
      }, 50);
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
      setError(null);
      return;
    }
    let cancelled = false;
    setProbeResolved(false);
    setError(null);
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
    sessionUserIdRef.current = null;
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
    return <p className="p-8 text-slate-600">Verifying owner portal access…</p>;
  }

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

  if (probeStatus === 403 || !probe?.owner_account_exists) {
    return <Navigate to="/access" replace state={{ reason: "owner_not_provisioned" }} />;
  }

  return (
    <PortalShell email={session.user.email} onSignOut={handleSignOut}>
      {children}
    </PortalShell>
  );
}
