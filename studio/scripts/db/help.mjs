// Prints help for DB type generation scripts.

const lines = [
  'DB Types (Supabase)',
  '',
  'Commands:',
  '  npm run db:generate         Generate TypeScript DB types from local Supabase',
  '  npm run db:check            Verify generated types match supabase/migrations/*.sql',
  '',
  'Legacy aliases (still supported):',
  '  npm run db:types:generate',
  '  npm run db:types:check',
  '',
  'Notes:',
  '  - Generation requires local Supabase running (e.g. `supabase db reset` or `supabase start`).',
  '  - The pre-commit hook runs `db:check` and will fail if migrations changed but types were not regenerated.',
]

console.log(lines.join('\n'))
