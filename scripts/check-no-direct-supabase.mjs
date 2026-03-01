#!/usr/bin/env node

import fs from 'node:fs/promises'
import path from 'node:path'

const ROOT = process.cwd()
const SRC_DIR = path.join(ROOT, 'src')

const ALLOWED_FILE_EXCEPTIONS = new Map([
  ['src/App.tsx', 'Temporary: auth session bootstrap until server session endpoint is in place.'],
  ['src/components/Layout.tsx', 'Temporary: auth sign-out delegation not migrated yet.'],
])

const ALLOWED_PREFIXES = ['src/services/', 'src/lib/supabase/']
const SCAN_EXTENSIONS = new Set(['.ts', '.tsx'])

const SUPABASE_CLIENT_IMPORT = /from\s+['"][^'"]*lib\/supabase(?:\/index)?['"]/g
const SUPABASE_PACKAGE_IMPORT = /import\s+(?!type\b)[^\n;]*from\s+['"]@supabase\/supabase-js['"]/g
const SUPABASE_RUNTIME_USAGE = /\bsupabase\.(auth|from|rpc|storage)\b/g

function toRepoPath(filePath) {
  return path.relative(ROOT, filePath).split(path.sep).join('/')
}

function isAllowedByPrefix(repoPath) {
  return ALLOWED_PREFIXES.some(prefix => repoPath.startsWith(prefix))
}

function isUiLayer(repoPath) {
  return (
    repoPath.startsWith('src/pages/') ||
    repoPath.startsWith('src/components/') ||
    repoPath.startsWith('src/ui/') ||
    repoPath.startsWith('src/hooks/')
  )
}

async function walk(dir) {
  const entries = await fs.readdir(dir, { withFileTypes: true })
  const files = []

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      files.push(...(await walk(fullPath)))
      continue
    }
    files.push(fullPath)
  }

  return files
}

function hasMatch(regex, text) {
  regex.lastIndex = 0
  return regex.test(text)
}

async function run() {
  const allFiles = await walk(SRC_DIR)
  const scanFiles = allFiles.filter(filePath => SCAN_EXTENSIONS.has(path.extname(filePath)))
  const violations = []

  for (const filePath of scanFiles) {
    const repoPath = toRepoPath(filePath)
    const content = await fs.readFile(filePath, 'utf8')
    const allowedByRule = isAllowedByPrefix(repoPath) || ALLOWED_FILE_EXCEPTIONS.has(repoPath)

    if (allowedByRule) continue

    if (hasMatch(SUPABASE_CLIENT_IMPORT, content)) {
      violations.push({
        file: repoPath,
        reason: 'Imports Supabase client from lib/supabase outside allowed layers.',
      })
    }

    if (isUiLayer(repoPath) && hasMatch(SUPABASE_PACKAGE_IMPORT, content)) {
      violations.push({
        file: repoPath,
        reason: 'Uses runtime @supabase/supabase-js import in UI layer (only type imports are allowed during migration).',
      })
    }

    if (isUiLayer(repoPath) && hasMatch(SUPABASE_RUNTIME_USAGE, content)) {
      violations.push({
        file: repoPath,
        reason: 'Uses supabase runtime API directly in UI layer.',
      })
    }
  }

  if (violations.length > 0) {
    process.stderr.write('[arch] Direct Supabase access guard failed.\n')
    for (const violation of violations) {
      process.stderr.write(` - ${violation.file}: ${violation.reason}\n`)
    }
    process.stderr.write('\nAllowed temporary exceptions:\n')
    for (const [file, note] of ALLOWED_FILE_EXCEPTIONS) {
      process.stderr.write(` - ${file}: ${note}\n`)
    }
    process.exit(1)
  }

  process.stdout.write('[arch] No forbidden direct Supabase access found in UI layers.\n')
}

run().catch(error => {
  process.stderr.write(`[arch] Guard check failed unexpectedly: ${error instanceof Error ? error.message : String(error)}\n`)
  process.exit(1)
})
