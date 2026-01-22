#!/usr/bin/env node
/**
 * i18n Missing Keys Detection for xScanner Studio
 *
 * Finds translation keys used in code but not defined in locale files.
 *
 * Usage: node scripts/i18n/check-missing.mjs
 * Exit codes: 0 = success, 1 = missing keys found
 */

import fs from 'fs/promises'
import path from 'path'
import { fileURLToPath } from 'url'
import { isDefinedKeyOrPluralVariant } from './helpers.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '../..')
const LOCALES_DIR = path.resolve(repoRoot, 'src', 'locales')
const BASE_LANG = 'de'
const SCAN_DIRS = ['src']
const SCAN_EXTENSIONS = new Set(['.ts', '.tsx', '.js', '.jsx', '.mjs'])
const PLURAL_SUFFIXES = ['_zero', '_one', '_two', '_few', '_many', '_other', '_plural']

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
  const singleQuotePattern = /\bt\s*\(\s*['"]([^'"]+)['"]/g
  let match

  while ((match = singleQuotePattern.exec(code)) !== null) {
    keys.add(match[1])
  }

  return keys
}

async function main() {
  console.log(`${colors.blue}🔎 Checking for missing i18n keys...${colors.reset}\n`)

  const basePath = path.join(LOCALES_DIR, BASE_LANG, 'translation.json')
  const baseJson = await readJson(basePath)
  const flat = flattenKeys(baseJson)
  const declaredKeys = new Set(flat.keys())

  const scanFiles = []
  for (const dir of SCAN_DIRS) {
    scanFiles.push(...(await listFiles(dir)))
  }

  const usedKeys = new Set()

  for (const file of scanFiles) {
    const code = await fs.readFile(file, 'utf8')
    const fileKeys = extractTranslationKeys(code)
    fileKeys.forEach(k => usedKeys.add(k))
  }

  const missing = []

  for (const key of usedKeys) {
    if (!isDefinedKeyOrPluralVariant(key, declaredKeys, PLURAL_SUFFIXES)) {
      missing.push(key)
    }
  }

  if (missing.length === 0) {
    console.log(`${colors.green}✅ No missing i18n keys found!${colors.reset}`)
    console.log(`   Scanned: ${scanFiles.length} files`)
    console.log(`   Used keys: ${usedKeys.size}`)
    process.exit(0)
  }

  console.error(
    `${colors.red}❌ Found ${missing.length} missing i18n key(s) (used in code but not defined):${colors.reset}\n`
  )

  missing.sort()
  missing.slice(0, 20).forEach(key => {
    console.error(`   - ${key}`)
  })

  if (missing.length > 20) {
    console.error(`   ... and ${missing.length - 20} more`)
  }

  console.error(`\n${colors.yellow}💡 Add these keys to ${BASE_LANG}/translation.json${colors.reset}`)

  process.exit(1)
}

main().catch(err => {
  console.error(`${colors.red}❌ Error: ${err.message}${colors.reset}`)
  process.exit(1)
})
