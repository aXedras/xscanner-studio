#!/usr/bin/env node

import fs from 'node:fs/promises'
import path from 'node:path'

const ROOT = process.cwd()
const SERVICES_DIR = path.join(ROOT, 'src', 'services')

const SCAN_EXTENSIONS = new Set(['.ts', '.tsx'])
const ALLOWED_PREFIXES = ['src/services/infrastructure/persistence/']
const ALLOWED_SEGMENT = '/repository/'

const SUPABASE_DB_CALL_PATTERN = /\bsupabase\s*\.\s*from\s*\(/g
const SUPABASE_RPC_CALL_PATTERN = /\bsupabase\s*\.\s*rpc\s*\(/g

function toRepoPath(filePath) {
  return path.relative(ROOT, filePath).split(path.sep).join('/')
}

function hasMatch(regex, text) {
  regex.lastIndex = 0
  return regex.test(text)
}

function isAllowedPath(repoPath) {
  if (repoPath.includes(ALLOWED_SEGMENT)) return true
  return ALLOWED_PREFIXES.some(prefix => repoPath.startsWith(prefix))
}

function countLinesUntil(content, index) {
  return content.slice(0, index).split('\n').length
}

function collectLineNumbers(content) {
  const lines = []
  SUPABASE_DB_CALL_PATTERN.lastIndex = 0
  SUPABASE_RPC_CALL_PATTERN.lastIndex = 0

  let match = SUPABASE_DB_CALL_PATTERN.exec(content)
  while (match) {
    lines.push(countLinesUntil(content, match.index))
    match = SUPABASE_DB_CALL_PATTERN.exec(content)
  }

  match = SUPABASE_RPC_CALL_PATTERN.exec(content)
  while (match) {
    lines.push(countLinesUntil(content, match.index))
    match = SUPABASE_RPC_CALL_PATTERN.exec(content)
  }

  return lines.sort((a, b) => a - b)
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

async function run() {
  const allFiles = await walk(SERVICES_DIR)
  const scanFiles = allFiles.filter(filePath => SCAN_EXTENSIONS.has(path.extname(filePath)))
  const violations = []

  for (const filePath of scanFiles) {
    const repoPath = toRepoPath(filePath)
    const content = await fs.readFile(filePath, 'utf8')

    const hasDbCall = hasMatch(SUPABASE_DB_CALL_PATTERN, content) || hasMatch(SUPABASE_RPC_CALL_PATTERN, content)
    if (!hasDbCall) continue

    if (isAllowedPath(repoPath)) continue

    const lines = collectLineNumbers(content)
    violations.push({ file: repoPath, lines })
  }

  if (violations.length > 0) {
    process.stderr.write('[arch] Supabase DB calls must stay in repository/persistence layers only.\n')
    for (const violation of violations) {
      const lineInfo = violation.lines.length > 0 ? ` (lines: ${violation.lines.join(', ')})` : ''
      process.stderr.write(` - ${violation.file}${lineInfo}\n`)
    }
    process.exit(1)
  }

  process.stdout.write('[arch] Supabase DB calls are centralized in repository/persistence layers.\n')
}

try {
  await run()
} catch (error) {
  process.stderr.write(`[arch] DB call guard failed unexpectedly: ${error instanceof Error ? error.message : String(error)}\n`)
  process.exit(1)
}
