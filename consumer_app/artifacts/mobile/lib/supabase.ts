import AsyncStorage from "@react-native-async-storage/async-storage";
import { setAuthTokenGetter } from "@workspace/api-client-react";
import * as Linking from "expo-linking";
import * as WebBrowser from "expo-web-browser";
import { Platform } from "react-native";
import { createClient, type AuthChangeEvent, type Session, type SupabaseClient } from "@supabase/supabase-js";

import { getAuthRedirectScheme, getSupabaseAnonKey, getSupabaseUrl, hasSupabaseAuthConfig } from "@/lib/env";

WebBrowser.maybeCompleteAuthSession();

let supabaseClient: SupabaseClient | null = null;

function getSupabaseClient(): SupabaseClient {
  if (supabaseClient) return supabaseClient;

  const supabaseUrl = getSupabaseUrl();
  const supabaseAnonKey = getSupabaseAnonKey();
  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Supabase Auth is not configured. Set EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY.",
    );
  }

  supabaseClient = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
    },
  });

  return supabaseClient;
}

function getOAuthRedirectUrl(): string {
  return Linking.createURL("auth/callback", {
    scheme: getAuthRedirectScheme(),
  });
}

async function signInWithOAuthProvider(provider: "google" | "facebook" | "apple") {
  const client = getSupabaseClient();
  const redirectTo = getOAuthRedirectUrl();

  const { data, error } = await client.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo,
      skipBrowserRedirect: true,
    },
  });

  if (error) throw error;
  if (!data.url) throw new Error("Supabase did not return an OAuth URL.");

  const result = await WebBrowser.openAuthSessionAsync(data.url, redirectTo);
  if (result.type !== "success") {
    throw new Error(`OAuth login was not completed: ${result.type}`);
  }

  return getCurrentSession();
}

export async function signInWithEmailPassword(email: string, password: string) {
  const client = getSupabaseClient();
  const { data, error } = await client.auth.signInWithPassword({ email, password });
  if (error) throw error;
  return data;
}

export async function signUpWithEmailPassword(email: string, password: string) {
  const client = getSupabaseClient();
  const { data, error } = await client.auth.signUp({ email, password });
  if (error) throw error;
  return data;
}

export async function signInWithGoogle() {
  return signInWithOAuthProvider("google");
}

export async function signInWithFacebook() {
  return signInWithOAuthProvider("facebook");
}

export async function signInWithAppleIOS() {
  if (Platform.OS !== "ios") {
    throw new Error("Apple Sign In is supported on iOS only.");
  }

  return signInWithOAuthProvider("apple");
}

export async function signOut() {
  const client = getSupabaseClient();
  const { error } = await client.auth.signOut();
  if (error) throw error;
}

export async function getCurrentSession(): Promise<Session | null> {
  if (!hasSupabaseAuthConfig()) return null;
  const client = getSupabaseClient();
  const { data, error } = await client.auth.getSession();
  if (error) throw error;
  return data.session;
}

export async function getAccessToken(): Promise<string | null> {
  const session = await getCurrentSession();
  return session?.access_token ?? null;
}

export function onAuthStateChange(
  listener: (event: AuthChangeEvent, session: Session | null) => void,
) {
  const client = getSupabaseClient();
  const { data } = client.auth.onAuthStateChange(listener);
  return data.subscription;
}

export function configureApiAuthTokenBridge() {
  setAuthTokenGetter(async () => getAccessToken());
}
