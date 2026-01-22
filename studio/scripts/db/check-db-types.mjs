import fs from 'node:fs'
import path from 'node:path'

import { computeMigrationsHash } from './schema-hash.mjs'

const repoRoot = path.resolve(process.cwd(), '..')
const migrationsDir = path.join(repoRoot, 'supabase', 'migrations')
const typesFile = path.join(process.cwd(), 'src', 'lib', 'supabase', 'database.types.ts')

const { hash: expectedHash } = computeMigrationsHash({ migrationsDir })

if (!fs.existsSync(typesFile)) {
  console.error('[db:types] Missing database types file:', typesFile)
  console.error('Run: (cd studio && npm run db:types:generate)')
  process.exit(1)
}

const content = fs.readFileSync(typesFile, 'utf8')
const match = content.match(/hash: ([a-f0-9]{64})/i)
const foundHash = match?.[1]

if (!foundHash) {
  console.error('[db:types] Could not find schema hash header in database.types.ts')
  console.error('Run: (cd studio && npm run db:types:generate)')
  process.exit(1)
}

if (foundHash !== expectedHash) {
  console.error('[db:types] Database types are out of date.')
  console.error(`Expected migrations hash: ${expectedHash}`)
  console.error(`Found in types file:     ${foundHash}`)
  console.error('Run: (cd studio && npm run db:types:generate)')
  process.exit(1)
}

console.log('[db:types] Database types are up to date.')
