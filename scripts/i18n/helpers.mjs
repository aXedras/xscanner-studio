/**
 * Shared i18n key usage helpers for xScanner Studio
 */

function levenshtein(a, b) {
  if (a === b) return 0
  if (!a.length) return b.length
  if (!b.length) return a.length

  const prev = new Array(b.length + 1)
  const curr = new Array(b.length + 1)
  for (let j = 0; j <= b.length; j++) prev[j] = j

  for (let i = 1; i <= a.length; i++) {
    curr[0] = i
    const ca = a.charCodeAt(i - 1)
    for (let j = 1; j <= b.length; j++) {
      const cb = b.charCodeAt(j - 1)
      const cost = ca === cb ? 0 : 1
      curr[j] = Math.min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost)
    }
    for (let j = 0; j <= b.length; j++) prev[j] = curr[j]
  }

  return prev[b.length]
}

/**
 * Expands used keys to include plural variants
 */
export function expandUsedKeys(usedKeys, declaredKeys, pluralSuffixes) {
  const expanded = new Set(usedKeys)

  const markPluralVariants = base => {
    for (const suffix of pluralSuffixes) {
      const variant = `${base}${suffix}`
      if (declaredKeys.has(variant)) expanded.add(variant)
    }
  }

  for (const key of usedKeys) {
    markPluralVariants(key)

    for (const suffix of pluralSuffixes) {
      if (key.endsWith(suffix)) {
        const base = key.slice(0, -suffix.length)
        if (declaredKeys.has(base)) expanded.add(base)
        markPluralVariants(base)
      }
    }
  }

  return expanded
}

/**
 * Treats `common.<rest>` as used when a feature key overrides it
 */
export function expandUsedWithOverriddenCommonKeys(usedKeys, commonRests, overridableScopes) {
  const expanded = new Set(usedKeys)

  for (const key of usedKeys) {
    for (const scope of overridableScopes) {
      const prefix = `${scope}.`
      if (!key.startsWith(prefix)) continue

      const rest = key.slice(prefix.length)
      if (!commonRests.has(rest)) continue

      expanded.add(`common.${rest}`)
    }
  }

  return expanded
}

/**
 * Detects suspiciously similar action verbs under strict prefixes
 */
export function findSuspiciousCommonStrictActionVariants(commonRests, strictOverridePrefixes, maxDistance = 2) {
  const strictPrefixes = strictOverridePrefixes.map(p => `${p}.`)

  const actionsByPrefix = new Map()

  for (const rest of commonRests) {
    const prefix = strictPrefixes.find(p => rest.startsWith(p))
    if (!prefix) continue

    const parts = rest.split('.')
    if (parts.length < 2) continue

    const strictPrefix = parts[0]
    const action = parts[1]

    if (!actionsByPrefix.has(strictPrefix)) actionsByPrefix.set(strictPrefix, new Set())
    actionsByPrefix.get(strictPrefix).add(action)
  }

  const pairs = []

  for (const [strictPrefix, actions] of actionsByPrefix.entries()) {
    const list = [...actions].sort()

    for (let i = 0; i < list.length; i++) {
      for (let j = i + 1; j < list.length; j++) {
        const a = list[i]
        const b = list[j]
        const d = levenshtein(a, b)

        if (d <= maxDistance) {
          pairs.push({ strictPrefix, a, b, d })
        }
      }
    }
  }

  pairs.sort(
    (x, y) =>
      x.strictPrefix.localeCompare(y.strictPrefix) || x.d - y.d || x.a.localeCompare(y.a) || x.b.localeCompare(y.b)
  )

  return pairs
}

/**
 * Checks if a key is defined (including plural variants)
 */
export function isDefinedKeyOrPluralVariant(key, declaredKeys, pluralSuffixes) {
  if (declaredKeys.has(key)) return true

  for (const suffix of pluralSuffixes) {
    if (declaredKeys.has(`${key}${suffix}`)) return true
  }

  return false
}
