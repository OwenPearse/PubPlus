import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";

import { getOwnerClaimsSummary } from "@/shared/lib/api";

const NAV_ITEMS: Array<{
  to: string;
  label: string;
  showOpenCount?: boolean;
}> = [
  { to: "/internal/founder-venues", label: "Founder venues" },
  { to: "/internal/owner-claims", label: "Owner claims", showOpenCount: true },
];

function navLinkClass(active: boolean) {
  return `inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium ${
    active
      ? "bg-slate-900 text-white"
      : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
  }`;
}

export function AdminInternalNav() {
  const location = useLocation();
  const [openCount, setOpenCount] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    void getOwnerClaimsSummary()
      .then(({ data }) => {
        if (active) setOpenCount(data.open_count);
      })
      .catch(() => {
        if (active) setOpenCount(null);
      });
    return () => {
      active = false;
    };
  }, [location.pathname]);

  return (
    <nav
      aria-label="Internal admin"
      className="border-b border-slate-200 bg-slate-50 px-4 py-2"
    >
      <div className="mx-auto flex max-w-7xl flex-wrap gap-2">
        {NAV_ITEMS.map((item) => {
          const active =
            location.pathname === item.to || location.pathname.startsWith(`${item.to}/`);
          return (
            <Link key={item.to} to={item.to} className={navLinkClass(active)}>
              {item.label}
              {item.showOpenCount && openCount !== null && openCount > 0 ? (
                <span
                  className={`inline-flex min-w-[1.25rem] items-center justify-center rounded-full px-1.5 py-0.5 text-xs font-semibold ${
                    active ? "bg-white text-slate-900" : "bg-amber-100 text-amber-900"
                  }`}
                >
                  {openCount}
                </span>
              ) : null}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
