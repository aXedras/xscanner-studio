# Logging — xScanner Studio

Structured logging for the frontend application.

---

## Foundation

Logs exist for one reason:
→ **Understanding what happened when something breaks**

Not:
- To prove the code ran
- To track every detail

But:
- To debug production issues
- To understand system behavior
- To trace errors to their source

---

## Core Rules

### 1. Always Use Logger Abstraction

**Never use console directly.**

```typescript
// ❌ NEVER
console.log('Loading extractions...')
console.error('Failed:', error)

// ✅ ALWAYS
import { logger } from '@/lib/logging'
logger.debug('ExtractionService', 'Loading extractions', { count: 10 })
logger.error('ExtractionService', 'Failed to load', error)
```

**Why:**
- Filterable via environment
- Testable (can be mocked)
- Consistent format
- Production-ready (can be disabled)

### 2. Configuration

**Development (.env.local):**
```bash
VITE_LOG_LEVEL=debug           # See all logs
VITE_LOG_CATEGORIES=ExtractionService,SupabaseClient  # Filter specific categories

# Optional: persist browser logs to a local file while running `npm run dev`
VITE_LOG_TO_FILE=true
VITE_LOG_INGEST_PATH=/__studio_log

# Enable the Vite dev server log ingest endpoint (Node.js)
STUDIO_LOG_INGEST_ENABLED=true
STUDIO_LOG_INGEST_PATH=/__studio_log

# Output file (relative to `studio/`)
STUDIO_LOG_FILE=../logs/studio.log

# Rolling config
STUDIO_LOG_MAX_BYTES=1048576
STUDIO_LOG_BACKUP_COUNT=5
```

**Production (.env):**
```bash
VITE_LOG_LEVEL=error           # Only errors
# or
VITE_LOG_LEVEL=none            # Completely disable

# NOTE: file logging is meant for local dev only.
# The file sink runs on the Vite dev server and is not part of the production build.
```

**Log Level Hierarchy:**
```
debug → info → warn → error → none
```

- `debug` → All logs visible
- `info` → info, warn, error visible (no debug)
- `error` → Only errors
- `none` → No logs at all

### 3. Log Levels

| Level | Purpose | Use For |
|-------|---------|---------|
| `debug` | Technical details | Discovery, state changes, API calls |
| `info` | Important events | User actions, workflows, success states |
| `warn` | Recoverable issues | Missing optional data, fallbacks |
| `error` | Failures | Exceptions, critical errors |

**Guidelines:**
- **debug**: Development only
- **info**: Keep in production for monitoring
- **warn**: Always investigate
- **error**: Always fix

### 4. Categories

Use consistent, descriptive categories (component/service names).

**Pattern:** PascalCase module/component name

```typescript
// Services
logger.debug('ExtractionService', 'Loading extraction', { id })
logger.debug('SupabaseClient', 'Querying table', { table: 'extractions' })

// Components
logger.debug('WelcomePage', 'Component mounted')
logger.debug('LoginDialog', 'Auth state changed', { user })

// Hooks
logger.debug('useExtractions', 'Fetching data')
logger.debug('useAuth', 'Session updated')
```

### 5. Structured Data (Context)

Always include relevant context as objects.

```typescript
// ✅ Good - Structured
logger.debug('ExtractionService', 'Loading extraction', {
  id: 'abc123',
  userId: 'user-xyz'
})

// ❌ Bad - String interpolation
logger.debug('ExtractionService', `Loading extraction ${id} for user ${userId}`)
```

**Why:**
- Easy to parse programmatically
- Filterable by fields
- Better debugging

### 6. Never Log Sensitive Data

**Never log:**
- Passwords or credentials
- API keys (full)
- Authentication tokens
- Personal data (email in full, names)

**Do log:**
- Metadata (timestamps, counts)
- Masked values (first/last few chars)
- Operation types
- IDs (UUIDs are safe)

---

## File Logging (Local Dev)

Studio can optionally write frontend logs to a rolling file at `logs/studio.log`.

This works by:
- The browser logger sending events to the Vite dev server (same origin)
- The dev server appending JSONL to a log file
- Rotating the log once it exceeds a configured size

### How To Enable

1. Enable the client-side shipper:
  - `VITE_LOG_TO_FILE=true`
  - `VITE_LOG_INGEST_PATH=/__studio_log`

2. Enable the dev server ingest endpoint:
  - `STUDIO_LOG_INGEST_ENABLED=true`
  - `STUDIO_LOG_INGEST_PATH=/__studio_log` (must match `VITE_LOG_INGEST_PATH`)

3. Configure output + rotation:
  - `STUDIO_LOG_FILE=../logs/studio.log`
  - `STUDIO_LOG_MAX_BYTES=1048576`
  - `STUDIO_LOG_BACKUP_COUNT=5`

Rotation behavior:
- When `studio.log` exceeds `STUDIO_LOG_MAX_BYTES`, it is renamed to `studio.log.1`
- Existing backups are shifted (`.1` → `.2`, …) up to `STUDIO_LOG_BACKUP_COUNT`

### Notes

- The log format is JSON Lines (one JSON object per line), suitable for grep/jq.
- The file sink is intentionally dev-only. Do not rely on it in production.
- The client logger performs basic redaction of obviously sensitive keys (password/token/secret/apiKey), but you must still avoid logging PII.

## Common Patterns

### Service Layer

```typescript
export class ExtractionService {
  async getExtraction(id: string) {
    logger.debug('ExtractionService', 'Loading extraction', { id })

    try {
      const { data, error } = await supabase
        .from('extractions')
        .select('*')
        .eq('id', id)
        .single()

      if (error) throw error

      logger.info('ExtractionService', 'Extraction loaded', { id })
      return data
    } catch (error) {
      logger.error('ExtractionService', 'Failed to load extraction', error)
      throw error
    }
  }
}
```

### React Components

```typescript
export default function ExtractionList() {
  useEffect(() => {
    logger.debug('ExtractionList', 'Component mounted')
    return () => {
      logger.debug('ExtractionList', 'Component unmounted')
    }
  }, [])

  const handleDelete = async (id: string) => {
    logger.info('ExtractionList', 'User initiated delete', { id })
    try {
      await deleteExtraction(id)
      logger.info('ExtractionList', 'Extraction deleted', { id })
    } catch (error) {
      logger.error('ExtractionList', 'Delete failed', error)
    }
  }

  return <div>...</div>
}
```

### Custom Hooks

```typescript
export function useExtractions() {
  const [data, setData] = useState<Extraction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    logger.debug('useExtractions', 'Fetching extractions')

    const fetchData = async () => {
      try {
        const extractions = await getExtractions()
        logger.info('useExtractions', 'Extractions loaded', { count: extractions.length })
        setData(extractions)
      } catch (error) {
        logger.error('useExtractions', 'Failed to fetch', error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return { data, loading }
}
```

### Error Handling

```typescript
try {
  await saveExtraction(data)
} catch (error) {
  logger.error('ExtractionForm', 'Save failed', error)

  // Show user-friendly message
  toast({
    title: 'Error',
    description: 'Failed to save extraction',
    variant: 'destructive'
  })

  // Re-throw if caller needs to handle
  throw error
}
```

---

## Advanced Features

### Performance Timing

```typescript
logger.time('LoadAllExtractions')
const extractions = await loadAllExtractions()
logger.timeEnd('LoadAllExtractions')
// Output: ⏱️ LoadAllExtractions: 234.56ms
```

### Grouped Logs

```typescript
logger.group('ExtractionService', 'Processing batch upload')
logger.debug('ExtractionService', 'Found 10 files')
logger.debug('ExtractionService', 'Uploading to storage...')
logger.debug('ExtractionService', 'Creating records...')
logger.groupEnd()
```

---

## Testing

Mock logger in tests:

```typescript
import { logger } from '@/lib/logging'

vi.mock('@/lib/logging', () => ({
  logger: {
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    time: vi.fn(),
    timeEnd: vi.fn(),
  }
}))

test('should log on error', async () => {
  await expect(doSomething()).rejects.toThrow()
  expect(logger.error).toHaveBeenCalledWith(
    'ServiceName',
    'Operation failed',
    expect.any(Error)
  )
})
```

---

## Best Practices

1. **One category per file/module** - Consistent naming
2. **Log at entry/exit of important operations** - Trace flow
3. **Always log errors with full context** - Include error object + data
4. **Use debug for discovery** - Disable in production
5. **Keep info logs meaningful** - What would you want to see in production?
6. **Include timing for slow operations** - Database queries, API calls
7. **Test error logging** - Verify errors are logged correctly

---

## Anti-Patterns

❌ **Don't:**
```typescript
// String interpolation
logger.debug('Service', `Loading ${id}`)

// console.log anywhere
console.log('Debug:', data)

// Logging in loops without context
items.forEach(item => logger.debug('Service', 'Processing'))

// Sensitive data
logger.debug('Auth', 'Password', { password })
```

✅ **Do:**
```typescript
// Structured data
logger.debug('Service', 'Loading', { id })

// Logger abstraction
logger.debug('Service', 'Debug', data)

// Aggregate in loops
logger.debug('Service', 'Processing items', { count: items.length })

// Masked sensitive data
logger.debug('Auth', 'Login attempt', { email: email.substring(0, 3) + '***' })
```
