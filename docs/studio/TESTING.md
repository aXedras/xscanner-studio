# Testing Strategy — xScanner Studio

How we test code in the frontend application.

---

## Foundation

Tests exist for one reason:
→ **Accountability for the reality we create**

Not:
- To meet coverage metrics
- Because "best practices" say so

But:
- Because code runs in production
- Because users depend on it
- Because errors have real consequences

---

## Core Principles

### 1. Test Reality, Not Fiction

**CRITICAL RULE: Never invent tests.**

Before writing any test:
1. Check the actual implementation
2. Verify which functions/components exist
3. Understand what they actually do
4. Write tests for the **real** behavior

**Forbidden:**
- ❌ Assuming functions exist without checking
- ❌ Inventing function signatures
- ❌ Writing tests based on "what should be there"
- ❌ Testing against imagined behavior

**Required:**
- ✅ Read the implementation first
- ✅ Verify exports exist
- ✅ Test actual public API
- ✅ Use real return types

**Why this matters:**
- Tests must reflect production reality
- Fictional tests create false confidence
- Reality changes - tests must track it

### 2. Test Behavior, Not Implementation

**Black-Box** = Test via public interface
- You don't know (or care) how it works internally
- You only test observable behavior
- Implementation can change freely

**White-Box** = Test knows internals
- You test against specific implementation
- Every change breaks tests
- Maintenance burden instead of safety

**Decision:**
→ Black-Box whenever possible
→ White-Box only when absolutely necessary

### 3. Test Types (Priority Order)

**1. Integration Tests (Default)**
- Definition (Studio): **real client → real xScanner API** over HTTP (happy path)
- Prerequisites: **xScanner API is running** and **Supabase is running/configured**
- If API/Supabase are not available: the integration tests **must fail** (this is a hard precondition)
- More confidence, fewer tests; survives refactoring

**2. Component Tests (UI)**
- Render components with React Testing Library
- Test user interactions
- Verify rendered output
- No implementation details

**3. Unit Tests (Black-Box, Fast)**
- Prefer **black-box**: test via the public API (stable under refactors)
- Use for critical behavior that we don't want to re-validate via network tests every time (e.g. HTTP error mapping)
- Mock external boundaries (e.g. `fetch`) but keep assertions on observable behavior (inputs/outputs/errors)
- Use pure-function unit tests where they make sense (calculations, utils), but not limited to “algorithms”

**4. E2E Tests (Critical Paths)**
- Playwright for user flows
- Login → Upload → View → Edit
- Most expensive, highest confidence

---

## Testing Stack

### Vitest
- Test runner
- Fast, Vite-native
- Compatible with Jest API

### React Testing Library
- Component testing
- User-centric queries
- No implementation details

### Playwright (Future)
- E2E testing
- Real browser automation
- Critical user journeys

---

## Test Structure

### File Organization

```
studio/
├── src/
│   └── ...
└── tests/
  ├── setup.ts
  ├── unit/
  │   └── HttpXScannerClient.test.ts
  └── integration/
    └── xScanner.test.ts
```

Integration tests require real dependencies. Configure the API base URL via Studio env (`studio/.env.local`):

- `VITE_API_URL=http://localhost:8000`

Fallback behavior (no extra env vars):
- If `VITE_API_URL` is not set, tests use the standard default `http://localhost:8000`.

Note: Studio has its own environment.

- Studio runtime uses `.env.local` / `.env` in `studio/` (Vite, `VITE_*`).
- Studio tests (Vitest/Node) read from `process.env.*` and we load the Studio `.env*` files for tests too.
- The xScanner API server loads its own `.env`/`.env.local` independently (separate process).

---

## Orders: upload and extract (PDF + images)

The Orders upload UI supports two upload modes:

- **PDF**: uploads a single PDF file.
- **Images**: uploads one or more image files (multiple pages).

### Request shape

The Studio client sends `multipart/form-data` with different field names depending on the upload mode:

- **PDF mode**: `file` (single part)
- **Images mode**: `files` (repeated parts, one per image)

Query parameters used by the UI:

- `strategy`: extraction strategy (e.g. `cloud`)
- `use_mock`: `true|false`
- `debug`: `true|false` (only on the debug endpoint)

### Mock mode

When `use_mock=true`, the server loads recorded fixtures from:

- `src/xscanner/mockdata/order_extract/` (extract fixtures)
- `src/xscanner/mockdata/order_vision/` (vision marker-text fixtures)

For image uploads (and scanned PDFs that require vision), you need **both** a vision fixture and an extract fixture for the same upload filename.

To record fixtures from a local file:

- `make record-order-mocks FILE=invoices/<your-file>.pdf`
- `make record-order-mocks FILE=invoices/<your-file>.jpg`

To record a full strategy-level mock fixture (no sub-step mocks required):

- `make record-order-mock STRATEGY=manual FILE=invoices/<your-file>.pdf`
- `make record-order-mock STRATEGY=cloud FILE=invoices/<your-file>.pdf`

Example:
- Set `VITE_API_URL` in `studio/.env.local`
- Run: `npm run test:integration`

### Naming Convention

- Test files: `*.test.ts` or `*.test.tsx`
- Test suites: `describe('ComponentName', () => {})`
- Test cases: `test('should do something', () => {})`

---

## Common Patterns

### Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import WelcomePage from './WelcomePage'

describe('WelcomePage', () => {
  test('should render welcome message', () => {
    const mockUser = { email: 'test@example.com' }
    render(<WelcomePage user={mockUser} />)

    expect(screen.getByText(/willkommen zurück/i)).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  test('should call signOut when logout clicked', async () => {
    const mockUser = { email: 'test@example.com' }
    const mockSignOut = vi.fn()

    // Mock supabase
    vi.mock('@/lib/supabase', () => ({
      supabase: { auth: { signOut: mockSignOut } }
    }))

    render(<WelcomePage user={mockUser} />)

    const logoutBtn = screen.getByRole('button', { name: /logout/i })
    fireEvent.click(logoutBtn)

    expect(mockSignOut).toHaveBeenCalled()
  })
})
```

### Service Tests

```typescript
import { describe, test, expect, beforeEach, afterEach, vi } from 'vitest'
import { ExtractionService } from './extractionService'
import { supabase } from '@/lib/supabase'

vi.mock('@/lib/supabase')

describe('ExtractionService', () => {
  let service: ExtractionService

  beforeEach(() => {
    service = new ExtractionService()
    vi.clearAllMocks()
  })

  test('should load extraction by id', async () => {
    const mockData = { id: '123', serial_number: 'ABC-001' }

    vi.mocked(supabase.from).mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: mockData, error: null })
        })
      })
    } as any)

    const result = await service.getExtraction('123')

    expect(result).toEqual(mockData)
    expect(supabase.from).toHaveBeenCalledWith('extractions')
  })

  test('should throw on error', async () => {
    const mockError = new Error('Database error')

    vi.mocked(supabase.from).mockReturnValue({
      select: vi.fn().mockReturnValue({
        eq: vi.fn().mockReturnValue({
          single: vi.fn().mockResolvedValue({ data: null, error: mockError })
        })
      })
    } as any)

    await expect(service.getExtraction('123')).rejects.toThrow('Database error')
  })
})
```

### Hook Tests

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { describe, test, expect, vi } from 'vitest'
import { useExtractions } from './useExtractions'

vi.mock('@/lib/supabase')

describe('useExtractions', () => {
  test('should fetch extractions on mount', async () => {
    const mockData = [
      { id: '1', serial_number: 'ABC-001' },
      { id: '2', serial_number: 'ABC-002' }
    ]

    vi.mocked(supabase.from).mockReturnValue({
      select: vi.fn().mockResolvedValue({ data: mockData, error: null })
    } as any)

    const { result } = renderHook(() => useExtractions())

    expect(result.current.loading).toBe(true)

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(result.current.data).toEqual(mockData)
  })
})
```

---

## Test Configuration

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

### Test Setup (src/test/setup.ts)

```typescript
import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

// Mock environment variables
vi.mock('import.meta', () => ({
  env: {
    VITE_SUPABASE_URL: 'http://localhost:54321',
    VITE_SUPABASE_ANON_KEY: 'test-key',
    VITE_LOG_LEVEL: 'none',
  }
}))
```

---

## Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific file
npm test -- src/components/WelcomePage.test.tsx

# UI mode
npm test -- --ui
```

---

## Best Practices

### DO ✅

1. **Test user behavior, not implementation**
   ```typescript
   // ✅ Good
   expect(screen.getByText('Welcome')).toBeInTheDocument()

   // ❌ Bad
   expect(component.state.showWelcome).toBe(true)
   ```

2. **Use user-centric queries**
   ```typescript
   // ✅ Good
   screen.getByRole('button', { name: /logout/i })
   screen.getByLabelText('Email')

   // ❌ Bad
   screen.getByTestId('logout-btn')
   ```

3. **Mock external dependencies**
   ```typescript
   // Supabase, API calls, localStorage
   vi.mock('@/lib/supabase')
   ```

4. **Test error states**
   ```typescript
   test('should show error message on failure', async () => {
     // Mock error response
     // Trigger action
     // Verify error shown
   })
   ```

5. **Keep tests isolated**
   ```typescript
   beforeEach(() => {
     vi.clearAllMocks()
   })
   ```

### DON'T ❌

1. **Don't test implementation details**
   ```typescript
   // ❌ Don't
   expect(component.state.count).toBe(5)
   expect(mockFunction).toHaveBeenCalledTimes(3)

   // ✅ Do
   expect(screen.getByText('Count: 5')).toBeInTheDocument()
   ```

2. **Don't test library code**
   ```typescript
   // ❌ Don't test React, Supabase internals
   ```

3. **Don't use implementation-specific selectors**
   ```typescript
   // ❌ Don't
   container.querySelector('.my-class')

   // ✅ Do
   screen.getByRole('button')
   ```

4. **Don't ignore async operations**
   ```typescript
   // ❌ Don't
   fireEvent.click(button)
   expect(screen.getByText('Done')).toBeInTheDocument()

   // ✅ Do
   fireEvent.click(button)
   await waitFor(() => {
     expect(screen.getByText('Done')).toBeInTheDocument()
   })
   ```

---

## Coverage Goals

**Target: 80% coverage for critical paths**

- Services: 90%+ (business logic)
- Components: 70%+ (UI behavior)
- Utils: 90%+ (pure functions)
- Hooks: 80%+ (state management)

**Not about the number, but:**
- Critical user flows covered
- Error handling tested
- Edge cases verified

---

## CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
      - run: npm ci
      - run: npm test -- --coverage
```

**Rule: All tests must pass before merge**

---

## Anti-Patterns

❌ **Don't:**

```typescript
// Testing internal state
expect(component.state.isLoading).toBe(false)

// Testing implementation
expect(mockFn).toHaveBeenCalledTimes(3)

// Snapshot testing everything
expect(container).toMatchSnapshot()

// Async without waiting
fireEvent.click(button)
expect(screen.getByText('Done'))
```

✅ **Do:**

```typescript
// Test user-visible behavior
expect(screen.queryByText('Loading...')).not.toBeInTheDocument()

// Test outcomes
expect(screen.getByText('Success')).toBeInTheDocument()

// Selective snapshots
expect(formatDate(date)).toMatchInlineSnapshot('"Jan 18, 2026"')

// Wait for async
await waitFor(() => expect(screen.getByText('Done')).toBeInTheDocument())
```
