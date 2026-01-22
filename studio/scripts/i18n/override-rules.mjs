/**
 * Shared i18n override rules for xScanner Studio
 *
 * Prevents feature scopes from inventing new subtrees that should be common.
 */

export const OVERRIDABLE_SCOPES = ['extraction', 'auth']

// Strict prefixes: if a feature defines e.g. extraction.toast.save.*,
// a matching common.toast.save.* MUST exist.
export const STRICT_OVERRIDE_PREFIXES = ['toast', 'action', 'validation', 'status']

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

function suggestCommonKeys(restKey, commonRests, limit = 3) {
  const candidates = []
  const suffix = restKey.includes('.') ? restKey.slice(restKey.lastIndexOf('.')) : ''

  const strictPrefixes = STRICT_OVERRIDE_PREFIXES.map(p => `${p}.`)

  for (const candidate of commonRests) {
    if (!strictPrefixes.some(p => candidate.startsWith(p))) continue
    if (suffix && !candidate.endsWith(suffix)) continue
    candidates.push(candidate)
  }

  const pool = candidates.length
    ? candidates
    : [...commonRests].filter(c => strictPrefixes.some(p => c.startsWith(p)))

  return pool
    .map(c => ({ c, d: levenshtein(restKey, c) }))
    .sort((a, b) => a.d - b.d)
    .slice(0, limit)
    .map(x => `common.${x.c}`)
}

export function findInvalidOverrideKeys(allKeys, commonRests, options = {}) {
  const { includeSuggestions = false } = options
  const invalid = []

  for (const key of allKeys) {
    for (const scope of OVERRIDABLE_SCOPES) {
      const scopePrefix = `${scope}.`
      if (!key.startsWith(scopePrefix)) continue

      const rest = key.slice(scopePrefix.length)

      for (const overridePrefix of STRICT_OVERRIDE_PREFIXES) {
        const strictPrefix = `${overridePrefix}.`
        if (!rest.startsWith(strictPrefix)) continue

        if (!commonRests.has(rest)) {
          invalid.push({
            key,
            expectedCommonKey: `common.${rest}`,
            ...(includeSuggestions ? { suggestions: suggestCommonKeys(rest, commonRests) } : {}),
          })
        }
      }
    }
  }

  invalid.sort((a, b) => a.key.localeCompare(b.key))
  return invalid
}
