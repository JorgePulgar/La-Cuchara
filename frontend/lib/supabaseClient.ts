/**
 * frontend/lib/supabaseClient.ts
 * Initializes the Supabase JS client from environment variables.
 */

// TODO: conectar Supabase
import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL ?? "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? "";

if (!supabaseUrl || !supabaseAnonKey) {
    console.warn(
        "Supabase not connected: check environment variables. " +
        "NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY must be set in frontend/.env.local"
    );
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
