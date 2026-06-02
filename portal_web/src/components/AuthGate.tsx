import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import type { Session } from "@supabase/supabase-js";

import { formatApiError, internalAuthProbe } from "@/lib/api";
import { hasSupabaseAuthConfig } from "@/lib/env";
import {
  getCurrentSession,
  onAuthStateChange,
  signInWithPassword,
  signOut,
} from "@/lib/supabase";

type Props = {
  children: ReactNode;
};

export function AuthGate({ children }: Props) {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const [adminOk, setAdminOk] = useState<boolean | null>(null);
  const [error, setError] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

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

  async function handleSignIn(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      const next = await signInWithPassword(email.trim(), password);
      setSession(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed.");
    }
  }

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
    return (
      <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center p-6">
        <h1 className="mb-2 text-2xl font-bold">PubPlus Portal</h1>
        <p className="mb-6 text-sm text-slate-600">
          Sign in with an account that has internal admin access.
        </p>
        <form onSubmit={handleSignIn} className="space-y-4">
          <label className="block text-sm">
            Email
            <input
              type="email"
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="username"
            />
          </label>
          <label className="block text-sm">
            Password
            <input
              type="password"
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          {error ? <p className="text-sm text-red-700">{error}</p> : null}
          <button
            type="submit"
            className="w-full rounded bg-slate-900 py-2 text-white hover:bg-slate-800"
          >
            Sign in
          </button>
        </form>
      </div>
    );
  }

  if (adminOk === null) {
    return <p className="p-8 text-slate-600">Verifying internal admin access…</p>;
  }

  if (!adminOk) {
    return (
      <div className="mx-auto max-w-lg p-8">
        <h1 className="mb-2 text-xl font-bold">Access denied</h1>
        <p className="mb-4 text-sm text-slate-700">
          {error ||
            "Your account is signed in but does not have internal admin permission on this API."}
        </p>
        <button
          type="button"
          className="rounded border border-slate-300 px-4 py-2 text-sm"
          onClick={handleSignOut}
        >
          Sign out
        </button>
      </div>
    );
  }

  return (
    <div>
      <header className="border-b border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div>
            <p className="font-semibold">PubPlus Portal</p>
            <p className="text-xs text-slate-500">{session.user.email}</p>
          </div>
          <button
            type="button"
            className="text-sm text-slate-600 underline"
            onClick={handleSignOut}
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl p-4">{children}</main>
    </div>
  );
}
