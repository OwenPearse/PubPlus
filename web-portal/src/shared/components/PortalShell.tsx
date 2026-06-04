import type { ReactNode } from "react";

import { portalBrand } from "@/shared/lib/portalBrand";

type Props = {
  children: ReactNode;
  email?: string | null;
  onSignOut: () => void | Promise<void>;
};

export function PortalShell({ children, email, onSignOut }: Props) {
  return (
    <div>
      <header className="border-b border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img
              src={portalBrand.logoSrc}
              alt={portalBrand.logoAlt}
              className="h-8 w-8"
              width={32}
              height={32}
            />
            <div>
              <p className="font-semibold text-slate-900">{portalBrand.productName}</p>
              {email ? <p className="text-xs text-slate-500">{email}</p> : null}
            </div>
          </div>
          <button
            type="button"
            className="text-sm text-slate-600 underline"
            onClick={() => void onSignOut()}
          >
            Sign out
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl p-4">{children}</main>
    </div>
  );
}
