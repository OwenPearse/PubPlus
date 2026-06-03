import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";

import { hasSupabaseAuthConfig } from "@/lib/env";
import { getCurrentSession, onAuthStateChange } from "@/lib/supabase";

export function useAuthSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!hasSupabaseAuthConfig()) {
      setSession(null);
      setLoading(false);
      return;
    }

    let mounted = true;
    getCurrentSession()
      .then((currentSession) => {
        if (!mounted) return;
        setSession(currentSession);
      })
      .catch(() => {
        if (!mounted) return;
        setSession(null);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    let subscription: { unsubscribe: () => void } | null = null;
    try {
      subscription = onAuthStateChange((_event, nextSession) => {
        setSession(nextSession);
        setLoading(false);
      });
    } catch {
      setSession(null);
      setLoading(false);
    }

    return () => {
      mounted = false;
      subscription?.unsubscribe();
    };
  }, []);

  return {
    session,
    isAuthenticated: Boolean(session?.access_token),
    loading,
  };
}
