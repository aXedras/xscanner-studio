// Prints help for DB type generation scripts.

const lines = [
  'DB Types (Supabase)',
  '',
  'Commands:',
  '  npm run db:types:generate   Generate TypeScript DB types from local Supabase',
  '  npm run db:types:check      Verify generated types match supabase/migrations/*.sql',
  '',
  'Notes:',
  '  - Generation requires local Supabase running (e.g. `supabase db reset` or `supabase start`).',
  '  - The pre-commit hook runs `db:types:check` and will fail if migrations changed but types were not regenerated.',
]

console.log(lines.join('\n'))
