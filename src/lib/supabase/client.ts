import { createClient } from '@supabase/supabase-js'

import { getRuntimeEnv } from '../runtimeEnv'

const supabaseUrl = getRuntimeEnv('VITE_SUPABASE_URL') || import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = getRuntimeEnv('VITE_SUPABASE_ANON_KEY') || import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
