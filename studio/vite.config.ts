import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

import fs from 'node:fs'
import path from 'node:path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // Load ALL env vars for the dev server (not only VITE_*)
  const env = loadEnv(mode, process.cwd(), '')

  const ingestEnabled = env.STUDIO_LOG_INGEST_ENABLED === 'true'
  const ingestPath = env.STUDIO_LOG_INGEST_PATH || env.VITE_LOG_INGEST_PATH || '/__studio_log'
  const logFileRelative = env.STUDIO_LOG_FILE || '../logs/studio.log'
  const logFilePath = path.resolve(process.cwd(), logFileRelative)
  const maxBytes = Number(env.STUDIO_LOG_MAX_BYTES || '1048576')
  const backupCount = Number(env.STUDIO_LOG_BACKUP_COUNT || '5')

  let writeQueue = Promise.resolve()

  const rotateIfNeeded = async () => {
    try {
      const stat = await fs.promises.stat(logFilePath)
      if (!Number.isFinite(maxBytes) || maxBytes <= 0) return
      if (stat.size < maxBytes) return

      // Rotate: studio.log -> studio.log.1 -> ...
      for (let index = backupCount - 1; index >= 1; index -= 1) {
        const from = `${logFilePath}.${index}`
        const to = `${logFilePath}.${index + 1}`
        if (fs.existsSync(from)) {
          await fs.promises.rename(from, to)
        }
      }

      if (backupCount >= 1 && fs.existsSync(logFilePath)) {
        await fs.promises.rename(logFilePath, `${logFilePath}.1`)
      }
    } catch {
      // Ignore: file does not exist yet
    }
  }

  const appendLine = async (line: string) => {
    await fs.promises.mkdir(path.dirname(logFilePath), { recursive: true })
    await rotateIfNeeded()
    await fs.promises.appendFile(logFilePath, `${line}\n`, { encoding: 'utf8' })
  }

  return {
    plugins: [
      react(),
      {
        name: 'studio-log-ingest',
        configureServer(server) {
          if (!ingestEnabled) return

          server.middlewares.use(async (req, res, next) => {
            if (req.method !== 'POST' || req.url !== ingestPath) {
              next()
              return
            }

            let body = ''
            req.on('data', chunk => {
              body += chunk
              // Basic limit to avoid runaway payloads
              if (body.length > 100_000) {
                res.statusCode = 413
                res.end('Payload too large')
                req.destroy()
              }
            })

            req.on('end', () => {
              try {
                // Write as JSONL
                const parsed = JSON.parse(body)
                const line = JSON.stringify({
                  ts: new Date().toISOString(),
                  ...parsed,
                })

                writeQueue = writeQueue
                  .then(() => appendLine(line))
                  .then(() => {
                    res.statusCode = 204
                    res.end()
                  })
                  .catch(() => {
                    res.statusCode = 500
                    res.end('Failed to write log')
                  })
              } catch {
                res.statusCode = 400
                res.end('Invalid JSON')
              }
            })
          })
        },
      },
    ],
    server: {
      port: 8084,
      host: true,
    },
    resolve: {
      alias: {
        '@': '/src',
      },
    },
    build: {
      chunkSizeWarningLimit: 900,
    },
  }
})
