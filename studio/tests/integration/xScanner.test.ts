// @vitest-environment node

import { describe, expect, test } from 'vitest'

import { readFileSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

import type { ILogger } from '@/lib/utils/logging'
import { HttpXScannerClient } from '@/services/infrastructure/xscanner/HttpXScannerClient'

function createNoopLogger(): ILogger {
  return {
    debug: () => {},
    info: () => {},
    warn: () => {},
    error: () => {},
    time: () => {},
    timeEnd: () => {},
    group: () => {},
    groupEnd: () => {},
  }
}

function createTestImageFile(): File {
  // This test verifies Supabase persistence. The uploaded image is stored in DB/Storage,
  // so we use a small real bar image committed under `tests/fixtures/images/bars/`.
  const __filename = fileURLToPath(import.meta.url)
  const __dirname = path.dirname(__filename)
  const repoRoot = path.resolve(__dirname, '../../../')

  const filename = 'Gold_00500g_9999_D08744_Degussa.jpg'
  const imagePath = path.join(repoRoot, 'tests', 'fixtures', 'images', 'bars', filename)
  const bytes = readFileSync(imagePath)

  return new File([bytes], filename, { type: 'image/jpeg' })
}

async function fetchWithTimeout(url: string, timeoutMs: number): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = globalThis.setTimeout(() => controller.abort(), timeoutMs)

  try {
    return await fetch(url, { signal: controller.signal })
  } finally {
    globalThis.clearTimeout(timeoutId)
  }
}

async function fetchJsonWithTimeout<T>(url: string, timeoutMs: number): Promise<T> {
  const response = await fetchWithTimeout(url, timeoutMs)
  const text = await response.text().catch(() => '')

  if (!response.ok) {
    throw new Error(`Request failed (${response.status}) for ${url}. Body: ${text}`)
  }

  try {
    return JSON.parse(text) as T
  } catch (error) {
    throw new Error(`Invalid JSON from ${url}. Body: ${text}. Error: ${String(error)}`)
  }
}

function normalizeBaseUrl(input: string): string {
  const trimmed = input.replace(/\/+$/, '')

  try {
    const parsed = new URL(trimmed)
    if (parsed.hostname === 'localhost') {
      parsed.hostname = '127.0.0.1'
      return parsed.toString().replace(/\/+$/, '')
    }
  } catch {
    // ignore: keep as-is
  }

  return trimmed
}

function describeHttpErrorDetails(error: unknown): string {
  if (!error || typeof error !== 'object') return ''

  const record = error as Record<string, unknown>
  if (record.name !== 'HttpError') return ''

  const kind = typeof record.kind === 'string' ? record.kind : ''
  const status = typeof record.status === 'number' ? String(record.status) : ''
  const response = typeof record.responseSnippet === 'string' ? record.responseSnippet : ''

  return ` kind=${kind} status=${status} response=${response}`
}

describe('xScanner API (integration)', () => {
  test(
    'POST /extract/upload hits real server (use_mock=true) and persists (Supabase)',
    async () => {
      const baseUrl = process.env.VITE_API_URL ?? 'http://127.0.0.1:8000'
      const normalizedBaseUrl = normalizeBaseUrl(baseUrl)

      // Fast precondition checks (fail early with actionable errors).
      try {
        const health = await fetchWithTimeout(`${normalizedBaseUrl}/health`, 1_500)
        if (![200, 503, 500].includes(health.status)) {
          const body = await health.text().catch(() => '')
          throw new Error(
            `xScanner API health check failed (${health.status}) at ${normalizedBaseUrl}/health. Body: ${body}`
          )
        }
      } catch (error) {
        throw new Error(
          `xScanner API not reachable at ${normalizedBaseUrl}. ` +
            `Start the API and Supabase. Optionally configure studio/.env.local with VITE_API_URL. Root error: ${String(error)}`
        )
      }

      const config = await fetchJsonWithTimeout<{
        supabase?: { url_set?: boolean; service_role_key_set?: boolean }
      }>(`${normalizedBaseUrl}/config`, 1_500)

      const supabaseUrlSet = Boolean(config.supabase?.url_set)
      const supabaseKeySet = Boolean(config.supabase?.service_role_key_set)
      if (!supabaseUrlSet || !supabaseKeySet) {
        throw new Error(
          `Supabase persistence not configured on xScanner API. ` +
            `Expected /config supabase.url_set=true and supabase.service_role_key_set=true, got ` +
            `url_set=${String(supabaseUrlSet)} service_role_key_set=${String(supabaseKeySet)}. ` +
            `Start Supabase and ensure SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set for the API process.`
        )
      }

      const client = new HttpXScannerClient(createNoopLogger(), normalizedBaseUrl, { timeoutMs: 15_000 })
      const file = createTestImageFile()

      let result: Awaited<ReturnType<HttpXScannerClient['extractFromUpload']>>
      try {
        result = await client.extractFromUpload({
          file,
          strategy: 'cloud',
          useMock: true,
          registerOnBil: false,
        })
      } catch (error) {
        const details = describeHttpErrorDetails(error)
        throw new Error(
          `POST ${normalizedBaseUrl}/extract/upload did not complete successfully. ` +
            `If API+Supabase are running, check the API logs for Supabase persistence timeouts/DNS issues. ` +
            `Root error: ${String(error)}${details}`
        )
      }

      if (!result.success) {
        throw new Error(
          `Expected success=true from /extract/upload (mock mode) but got success=false. ` +
            `error=${String(result.error ?? '')}`
        )
      }

      expect(result.success).toBe(true)
      expect(typeof result.request_id).toBe('string')
      expect(result.request_id.length).toBeGreaterThan(0)
      expect(result.structured_data).toBeTruthy()

      // Integration definition: Supabase must be running/configured.
      // The server persists even in mock mode; if persistence is disabled, extraction_id will be missing.
      expect(typeof result.extraction_id).toBe('string')
      expect(result.extraction_id?.length).toBeGreaterThan(0)
    },
    30_000
  )
})
