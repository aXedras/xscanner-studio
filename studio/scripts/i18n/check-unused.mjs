#!/usr/bin/env node
/**
 * i18n Unused Keys Detection for xScanner Studio
 *
 * Finds translation keys defined in locale files but not used in code.
 *
 * Usage: node scripts/i18n/check-unused.mjs
 * Exit codes: 0 = success, 1 = unused keys found
 */

import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'
import { OVERRIDABLE_SCOPES } from './override-rules.mjs'
import { expandUsedKeys, expandUsedWithOverriddenCommonKeys } from './helpers.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '../..')
const LOCALES_DIR = path.resolve(repoRoot, 'src', 'locales')
const BASE_LANG = 'de'
const SCAN_DIRS = ['src', 'scripts']
const SCAN_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs'])
const PLURAL_SUFFIXES = ['_zero', '_one', '_two', '_few', '_many', '_other', '_plural']

// Namespaces that are allowed to have unused keys (reserved for future use)
const EXCLUDED_NAMESPACES = ['common']

const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
}

function isPlainObject(value) {
  return Object.prototype.toString.call(value) === '[object Object]'
}

async function readJson(absPath) {
  const raw = await fs.readFile(absPath, 'utf8')
  return JSON.parse(raw)
}

function flattenKeys(obj, prefix = '') {
  const result = new Map()

  function walk(value, prefix) {
    if (isPlainObject(value)) {
      for (const [key, next] of Object.entries(value)) {
        const nextKey = prefix ? `${prefix}.${key}` : key
        walk(next, nextKey)
      }
      return
    }
    if (prefix) result.set(prefix, value)
  }

  walk(obj, '')
  return result
}

async function listFiles(relDir) {
  const absDir = path.resolve(repoRoot, relDir)
  const out = []

  async function walk(dir) {
    const entries = await fs.readdir(dir, { withFileTypes: true })
    for (const entry of entries) {
      if (entry.name.startsWith('.')) continue

      const abs = path.join(dir, entry.name)

      if (entry.isDirectory()) {
        if (abs.includes(`${path.sep}locales${path.sep}`)) continue
        if (entry.name === 'node_modules' || entry.name === 'dist') continue
        await walk(abs)
        continue
      }

      if (!entry.isFile()) continue
      const ext = path.extname(entry.name)
      if (!SCAN_EXTENSIONS.has(ext)) continue

      out.push(abs)
    }
  }

  try {
    await walk(absDir)
  } catch {
    return []
  }

  return out.sort()
}

function extractTranslationKeys(code) {
  const keys = new Set()

  // Match t('key') or t("key")
  const pattern = /\bt\s*\(\s*['"]([^'"]+)['"]/g
  let match

  while ((match = pattern.exec(code)) !== null) {
    keys.add(match[1])
  }

  return keys
}

function extractDeclaredKeyLiterals(code, declaredKeys) {
  const keys = new Set()

  // Capture string literals and treat them as used keys iff they match a declared i18n key.
  // This supports dynamic patterns like: t(getLabelKey(x)) where getLabelKey returns a literal key.
  const pattern = /['"]([^'"]+)['"]/g
  let match
  while ((match = pattern.exec(code)) !== null) {
    const value = match[1]
    if (declaredKeys.has(value)) keys.add(value)
  }

  return keys
}

async function main() {
  console.log(`${colors.blue}🔎 Checking for unused i18n keys...${colors.reset}\n`)

  const basePath = path.join(LOCALES_DIR, BASE_LANG, 'translation.json')
  const baseJson = await readJson(basePath)
  const flat = flattenKeys(baseJson)
  const declaredKeys = new Set(flat.keys())

  const scanFiles = []
  for (const dir of SCAN_DIRS) {
    scanFiles.push(...(await listFiles(dir)))
  }

  let usedKeys = new Set()

  for (const file of scanFiles) {
    const code = await fs.readFile(file, 'utf8')
    const fileKeys = extractTranslationKeys(code)
    fileKeys.forEach(k => usedKeys.add(k))

    const literalKeys = extractDeclaredKeyLiterals(code, declaredKeys)
    literalKeys.forEach(k => usedKeys.add(k))
  }

  // Expand used keys to include plural variants
  usedKeys = expandUsedKeys(usedKeys, declaredKeys, PLURAL_SUFFIXES)

  // Mark common.* keys as used if feature overrides exist
  const commonRests = new Set(
    [...declaredKeys].filter(k => k.startsWith('common.')).map(k => k.slice('common.'.length))
  )
  usedKeys = expandUsedWithOverriddenCommonKeys(usedKeys, commonRests, OVERRIDABLE_SCOPES)

  const unused = []

  for (const key of declaredKeys) {
    if (!usedKeys.has(key)) {
      // Skip keys from excluded namespaces
      const namespace = key.split('.')[0]
      if (!EXCLUDED_NAMESPACES.includes(namespace)) {
        unused.push(key)
      }
    }
  }

  if (unused.length === 0) {
    console.log(`${colors.green}✅ No unused i18n keys found!${colors.reset}`)
    console.log(`   Declared: ${declaredKeys.size} keys`)
    console.log(`   Used: ${usedKeys.size} keys`)
    if (EXCLUDED_NAMESPACES.length > 0) {
      console.log(`   Excluded namespaces: ${EXCLUDED_NAMESPACES.join(', ')}`)
    }
    process.exit(0)
  }

  console.error(
    `${colors.red}❌ Found ${unused.length} unused i18n key(s) (defined but not used in code):${colors.reset}\n`
  )

  unused.sort()
  unused.slice(0, 20).forEach(key => {
    console.error(`   - ${key}`)
  })

  if (unused.length > 20) {
    console.error(`   ... and ${unused.length - 20} more`)
  }

  console.error(`\n${colors.yellow}💡 Consider removing these keys from translation files${colors.reset}`)

  process.exit(1)
}

main().catch(err => {
  console.error(`${colors.red}❌ Error: ${err.message}${colors.reset}`)
  process.exit(1)
})
