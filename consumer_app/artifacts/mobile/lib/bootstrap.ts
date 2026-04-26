import { setBaseUrl } from "@workspace/api-client-react";

import { getApiBaseUrl } from "@/lib/env";
import { configureApiAuthTokenBridge } from "@/lib/supabase";

let configured = false;

export function initializeApiAndAuthBridge() {
  if (configured) return;
  setBaseUrl(getApiBaseUrl());
  configureApiAuthTokenBridge();
  configured = true;
}
