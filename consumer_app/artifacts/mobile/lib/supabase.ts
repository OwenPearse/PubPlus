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
  if (Platform.OS === "web") {
    return Linking.createURL("auth/callback");
  }

  return Linking.createURL("auth/callback", {
    scheme: getAuthRedirectScheme(),
  });
}

function getRedirectParams(url: string): URLSearchParams {
  const queryStart = url.indexOf("?");
  const hashStart = url.indexOf("#");
  const params = new URLSearchParams();

  if (queryStart >= 0) {
    const queryEnd = hashStart >= 0 ? hashStart : undefined;
    const query = url.slice(queryStart + 1, queryEnd);
    new URLSearchParams(query).forEach((value, key) => params.set(key, value));
  }

  if (hashStart >= 0) {
    const hash = url.slice(hashStart + 1);
    new URLSearchParams(hash).forEach((value, key) => params.set(key, value));
  }

  return params;
}

async function completeOAuthSessionFromUrl(client: SupabaseClient, url: string): Promise<Session | null> {
  const params = getRedirectParams(url);
  const errorDescription = params.get("error_description") ?? params.get("error");
  if (errorDescription) {
    throw new Error(errorDescription);
  }

  const code = params.get("code");
  if (code) {
    const { data, error } = await client.auth.exchangeCodeForSession(code);
    if (error) throw error;
    return data.session;
  }

  const accessToken = params.get("access_token");
  const refreshToken = params.get("refresh_token");
  if (accessToken && refreshToken) {
    const { data, error } = await client.auth.setSession({
      access_token: accessToken,
      refresh_token: refreshToken,
    });
    if (error) throw error;
    return data.session;
  }

  throw new Error("OAuth redirect did not include a session.");
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

  return completeOAuthSessionFromUrl(client, result.url);
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
