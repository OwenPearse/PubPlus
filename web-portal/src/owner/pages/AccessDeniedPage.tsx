import { useLocation, Link } from "react-router-dom";

import { portalBrand } from "@/shared/lib/portalBrand";
import { signOut } from "@/shared/lib/supabase";

type LocationState = {
  message?: string;
};

export function AccessDeniedPage() {
  const location = useLocation();
  const state = (location.state ?? {}) as LocationState;

  async function handleSignOut() {
    await signOut();
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-md flex-col justify-center p-6">
      <header className="mb-8 text-center">
        <img
          src={portalBrand.logoSrc}
          alt={portalBrand.logoAlt}
          className="mx-auto h-12 w-12"
          width={48}
          height={48}
        />
        <h1 className="mt-4 text-2xl font-bold text-slate-900">{portalBrand.productName}</h1>
      </header>
      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-900">Access not available</h2>
        <p className="mt-2 text-sm text-slate-600">
          {state.message ||
            "You are signed in, but this portal area is not available for your account. Venue access may require provisioning or approval."}
        </p>
        <div className="mt-6 flex flex-col gap-3">
          <Link to="/access" className="text-sm font-medium text-slate-900 underline">
            Back to sign-in
          </Link>
          <button
            type="button"
            className="text-left text-sm text-slate-600 underline"
            onClick={() => void handleSignOut()}
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
