import type { ResolvePortalRoleResult } from "@/shared/lib/portalRole";
import { getDefaultPathForRole } from "@/shared/lib/portalRole";

export function getPostAuthContinuePath(result: ResolvePortalRoleResult): string | null {
  if (result.role === "admin") return "/internal/founder-venues";
  if (result.role === "owner") {
    if (result.probe.next_step === "enroll_mfa") return null;
    return "/owner";
  }
  return null;
}

export function shouldShowAccessDenied(result: ResolvePortalRoleResult): boolean {
  if (result.role === "none" && result.reason === "no_access") return true;
  if (result.role === "error" && result.code === "dual_access") return true;
  if (result.role === "error") return true;
  return false;
}

export { getDefaultPathForRole };
