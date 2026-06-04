import {
  formatApiError,
  internalAuthProbe,
  isApiRequestError,
  ownerAuthProbe,
  type OwnerAuthProbeBody,
} from "@/shared/lib/api";
import { getAccessToken } from "@/shared/lib/supabase";

export type PortalRole = "admin" | "owner" | "none" | "expired" | "error";

export type ResolvePortalRoleResult =
  | { role: "admin" }
  | { role: "owner"; probe: OwnerAuthProbeBody }
  | { role: "none"; reason: "no_access" | "owner_not_provisioned"; ownerProbe?: OwnerAuthProbeBody }
  | { role: "expired" }
  | { role: "error"; message: string; code?: "dual_access" };

function isUnauthorized(error: unknown): boolean {
  return isApiRequestError(error) && error.code === "unauthorized";
}

async function ownerProbeIndicatesProvisionedAccount(): Promise<boolean> {
  try {
    const result = await ownerAuthProbe();
    return result.status === 200 && result.body.owner_account_exists;
  } catch {
    return false;
  }
}

export async function resolvePortalRole(): Promise<ResolvePortalRoleResult> {
  const token = await getAccessToken();
  if (!token) {
    return { role: "expired" };
  }

  try {
    await internalAuthProbe();
    if (await ownerProbeIndicatesProvisionedAccount()) {
      return {
        role: "error",
        code: "dual_access",
        message:
          "This account has both operator and owner access. Contact support to resolve access.",
      };
    }
    return { role: "admin" };
  } catch (adminError) {
    if (isUnauthorized(adminError)) {
      return { role: "expired" };
    }
  }

  try {
    const ownerResult = await ownerAuthProbe();
    if (ownerResult.status === 200) {
      return { role: "owner", probe: ownerResult.body };
    }
    if (ownerResult.body.error?.code === "owner_not_provisioned") {
      return {
        role: "none",
        reason: "owner_not_provisioned",
        ownerProbe: ownerResult.body,
      };
    }
    return { role: "none", reason: "no_access", ownerProbe: ownerResult.body };
  } catch (ownerError) {
    if (isUnauthorized(ownerError)) {
      return { role: "expired" };
    }
    return { role: "error", message: formatApiError(ownerError) };
  }
}

export function getDefaultPathForRole(result: ResolvePortalRoleResult): string {
  if (result.role === "admin") return "/internal/founder-venues";
  if (result.role === "owner") {
    if (result.probe.next_step === "enroll_mfa") return "/access";
    return "/owner";
  }
  if (result.role === "none" && result.reason === "owner_not_provisioned") {
    return "/access";
  }
  if (result.role === "none") return "/access/denied";
  if (result.role === "expired") return "/access?reason=session_expired";
  return "/access/denied";
}

export function ownerProbeRequiresMfaOnAccess(probe: OwnerAuthProbeBody): boolean {
  return probe.next_step === "enroll_mfa";
}
