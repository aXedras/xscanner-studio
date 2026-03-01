#!/usr/bin/env node
/**
 * i18n Translation Validation Script for xScanner Studio
 *
 * Validates that all language files have:
 * 1. Same keys (no missing translations)
 * 2. Same structure (nested objects)
 * 3. String leaf values (no null/arrays/numbers/booleans)
 * 4. No empty string values
 * 5. Same interpolation variables (e.g. {{field}})
 * 6. Strict override validation (feature scopes must have matching common.* keys)
 *
 * Usage: node scripts/i18n/check-i18n.mjs
 * Exit codes: 0 = success, 1 = validation errors found
 */

import fs from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'
import { findInvalidOverrideKeys } from './override-rules.mjs'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.resolve(__dirname, '../..')
const LOCALES_DIR = path.resolve(repoRoot, 'src', 'locales')
const LANGUAGES = ['de', 'en']
const BASE_LANG = 'de'

const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m',
}

let hasErrors = false

function isPlainObject(value) {
  return Object.prototype.toString.call(value) === '[object Object]'
}

function describeValue(value) {
  if (value === null) return 'null'
  if (Array.isArray(value)) return 'array'
  return typeof value
}

function flattenKeys(obj, prefix = '') {
  const result = {}

  if (!isPlainObject(obj)) {
    return result
  }

  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key

    if (isPlainObject(value)) {
      Object.assign(result, flattenKeys(value, fullKey))
    } else {
      result[fullKey] = value
    }
  }

  return result
}

function extractInterpolationVars(str) {
  if (typeof str !== 'string') return new Set()
  const matches = str.match(/\{\{(\w+)\}\}/g)
  return new Set(matches || [])
}

function setsEqual(a, b) {
  if (a.size !== b.size) return false
  for (const item of a) {
    if (!b.has(item)) return false
  }
  return true
}

function validateTranslations() {
  console.log(`${colors.yellow}🔍 Validating i18n translations...${colors.reset}\n`)

  const translations = {}
  const flatTranslations = {}

  // Load all translation files
  for (const lang of LANGUAGES) {
    const filePath = path.join(LOCALES_DIR, lang, 'translation.json')

    if (!fs.existsSync(filePath)) {
      console.error(`${colors.red}❌ Missing translation file: ${filePath}${colors.reset}`)
      hasErrors = true
      continue
    }

    try {
      const content = fs.readFileSync(filePath, 'utf8')
      translations[lang] = JSON.parse(content)

      if (!isPlainObject(translations[lang])) {
        console.error(
          `${colors.red}❌ ${lang}: translation.json must contain a JSON object at the root (got ${describeValue(translations[lang])})${colors.reset}`
        )
        hasErrors = true
        continue
      }

      flatTranslations[lang] = flattenKeys(translations[lang])
    } catch (error) {
      console.error(`${colors.red}❌ ${lang}: Failed to parse translation.json: ${error.message}${colors.reset}`)
      hasErrors = true
    }
  }

  if (hasErrors) return

  // Get all unique keys
  const allKeys = new Set()
  for (const lang of LANGUAGES) {
    Object.keys(flatTranslations[lang]).forEach((key) => allKeys.add(key))
  }

  // Check for missing keys
  for (const lang of LANGUAGES) {
    const keys = flatTranslations[lang]
    const missing = []

    for (const key of allKeys) {
      if (!(key in keys)) {
        missing.push(key)
      }
    }

    if (missing.length > 0) {
      console.error(`${colors.red}❌ ${lang}: Missing ${missing.length} translation key(s):${colors.reset}`)
      missing.slice(0, 10).forEach((key) => console.error(`   - ${key}`))
      if (missing.length > 10) {
        console.error(`   ... and ${missing.length - 10} more`)
      }
      hasErrors = true
    }
  }

  // Validate value types
  for (const lang of LANGUAGES) {
    const keys = flatTranslations[lang]

    for (const [key, value] of Object.entries(keys)) {
      // Check type
      if (typeof value !== 'string') {
        console.error(
          `${colors.red}❌ ${lang}: Key "${key}" must be a string (got ${describeValue(value)})${colors.reset}`
        )
        hasErrors = true
        continue
      }

      // Check empty strings
      if (value.trim() === '') {
        console.error(`${colors.red}❌ ${lang}: Key "${key}" has empty value${colors.reset}`)
        hasErrors = true
        continue
      }
    }
  }

  // Check interpolation variables match across languages
  if (LANGUAGES.length > 1) {
    const baseKeys = flatTranslations[BASE_LANG]
    const mismatches = []

    for (const key of allKeys) {
      const baseValue = baseKeys[key]
      if (typeof baseValue !== 'string') continue

      const baseVars = extractInterpolationVars(baseValue)

      for (const lang of LANGUAGES) {
        if (lang === BASE_LANG) continue

        const otherValue = flatTranslations[lang][key]
        if (typeof otherValue !== 'string') continue

        const otherVars = extractInterpolationVars(otherValue)

        if (!setsEqual(baseVars, otherVars)) {
          mismatches.push({
            key,
            base: [...baseVars].sort(),
            other: [...otherVars].sort(),
            lang,
          })
        }
      }
    }

    if (mismatches.length > 0) {
      console.error(`${colors.red}❌ Interpolation variables mismatch (${mismatches.length} key(s)):${colors.reset}`)
      mismatches.slice(0, 10).forEach((m) => {
        console.error(
          `   - ${m.key}: ${BASE_LANG}=[${m.base.join(', ')}] ${m.lang}=[${m.other.join(', ')}]`
        )
      })
      if (mismatches.length > 10) {
        console.error(`   ... and ${mismatches.length - 10} more`)
      }
      hasErrors = true
    }
  }

  // Validate strict overrides
  const allKeysList = [...allKeys]
  const commonRests = new Set(
    allKeysList.filter((k) => k.startsWith('common.')).map((k) => k.slice('common.'.length))
  )
  const invalid = findInvalidOverrideKeys(allKeysList, commonRests, { includeSuggestions: true })

  if (invalid.length > 0) {
    console.error(`${colors.red}❌ Invalid i18n overrides (${invalid.length}):${colors.reset}`)
    console.error(
      `${colors.yellow}   Rule: Feature scopes (extraction/auth) may only override toast/action/validation/status if matching common.* exists.${colors.reset}`
    )
    console.error(`${colors.yellow}   Fix: Add the missing common.* key first, then override in feature scope.${colors.reset}`)

    invalid.slice(0, 10).forEach((item) => {
      const suggestionText = item.suggestions?.length
        ? ` (did you mean ${item.suggestions.join(' or ')}?)`
        : ''
      console.error(`   - ${item.key} → missing ${item.expectedCommonKey}${suggestionText}`)
    })
    if (invalid.length > 10) {
      console.error(`   ... and ${invalid.length - 10} more`)
    }
    hasErrors = true
  }

  if (!hasErrors) {
    const totalKeys = allKeys.size
    console.log(`${colors.green}✅ i18n validation passed!${colors.reset}`)
    console.log(`   Languages: ${LANGUAGES.join(', ')}`)
    console.log(`   Total keys: ${totalKeys}`)
  } else {
    console.log(`\n${colors.red}❌ i18n validation failed!${colors.reset}`)
  }
}

validateTranslations()

process.exit(hasErrors ? 1 : 0)
