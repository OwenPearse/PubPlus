import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";

import { getCurrentSession, onAuthStateChange } from "@/lib/supabase";

export function useAuthSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    getCurrentSession()
      .then((currentSession) => {
        if (!mounted) return;
        setSession(currentSession);
      })
      .finally(() => {
        if (!mounted) return;
        setLoading(false);
      });

    const subscription = onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
      setLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  return {
    session,
    isAuthenticated: Boolean(session?.access_token),
    loading,
  };
}
