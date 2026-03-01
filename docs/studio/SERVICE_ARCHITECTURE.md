# Service Architecture — xScanner Studio

Defines how services are structured and initialized in xScanner Studio.

For persistence mechanics (Supabase, migrations, generated DB types), see [../PERSISTENCE.md](../PERSISTENCE.md).

For extraction domain semantics (versioning, QA correction workflow), see [../domains/EXTRACTION.md](../domains/EXTRACTION.md).

**Pattern:** Service Factory with Repository Pattern

This document focuses on patterns. Concrete extraction-domain services (including BIL registration persistence) are documented below.

---

## Directory Structure

```
src/services/
├── factory/
│   ├── ServiceContainer.ts    # Dependency container
│   └── ServiceFactory.ts      # Singleton factory
├── core/                      # Business domain services
│   └── {domain}/
│       ├── I{Service}.ts
│       ├── impl/{Service}.ts
│       ├── mock/{Service}Mock.ts
│       ├── repository/
│       └── types/
└── infrastructure/            # IO + technical utilities
  ├── http/                  # Shared fetch helpers (joinUrl, JSON/Form requests, HttpError)
  ├── persistence/           # Supabase SDK implementations (IO)
  ├── xscanner/              # HTTP client for xScanner Server (IO)
  └── logging/
    ├── ILogger.ts
    └── ConsoleLogger.ts
```

---

## Service Structure

Every service follows this structure:

```
services/core/{domain}/
├── I{Service}.ts           # Interface (Contract)
├── impl/
│   └── {Service}.ts        # Implementation
├── mock/
│   └── {Service}Mock.ts    # Mock for testing
├── repository/
│   ├── I{Repository}.ts    # Repository interface
│   └── {Repository}.ts     # Repository implementation
└── types/
    └── index.ts            # Domain types
```

**Example: Blog Service**

```
services/core/blog/
├── IBlogService.ts
├── impl/
│   └── BlogService.ts
├── mock/
│   └── BlogServiceMock.ts
├── repository/
│   ├── IBlogRepository.ts
│   └── BlogRepository.ts
└── types/
    └── index.ts
```

---

## Layer Responsibilities

### Service (Business Logic)

**Responsibilities:**
- Business logic and validation
- Orchestrates repository calls
- Uses logging
- Stateless

**Uses:**
- Repository (data access)
- Other services (via DI)
- Logger

**Does NOT use:**
- Direct data access (only via repository)
- UI components

### Repository (Data Access)

**Responsibilities:**
- Data access (files, DB, API)
- CRUD operations
- No business logic

**Uses:**
- Storage/File system
- Logger

**Does NOT use:**
- Other services
- Business logic

### Infrastructure (IO + Technical Utilities)

**Responsibilities:**
- IO implementation details (HTTP, Supabase SDK, browser APIs)
- Reusable low-level helpers that must touch IO
- Consistent error shaping and logging

**Examples in this repo:**
- `src/services/infrastructure/http/httpClient.ts`
  - Centralizes URL building (`joinUrl`)
  - Centralizes request/response handling (`createHttpJsonClient`)
  - Provides consistent errors (`HttpError`) and logging
- `src/services/infrastructure/xscanner/HttpXScannerClient.ts`
  - Implements the `IXScannerClient` contract via HTTP calls to xScanner Server

**Important:**
- Infrastructure modules should not import UI.
- Infrastructure modules should not contain business logic; they expose primitives and IO clients.

---

## External API Clients (xScanner Server)

xScanner Studio talks to xScanner Server via an explicit client interface, not via inheritance-based base classes.

**Contract (core):**
- `src/services/core/xscanner/IXScannerClient.ts`

**Implementation (infrastructure):**
- `src/services/infrastructure/xscanner/HttpXScannerClient.ts`

**Wiring (factory):**
- `src/services/factory/ServiceFactory.ts`

### Dependency Rule

- Domain services depend on the `IXScannerClient` interface.
- The HTTP implementation stays in `infrastructure/xscanner`.

This keeps dependencies honest:
- The domain orchestrates and maps DTOs into local state.
- The client only speaks HTTP and returns server-contract DTOs.

### Configuration

The xScanner Server base URL is configured via Vite env vars:
- `VITE_API_URL`
- Default: `http://localhost:8000`

---

## Extraction Domain: BIL Registrations

xScanner Studio reads BIL registration attempts from Supabase and presents them alongside extraction versions.

### Data Model

- Table: `bil_registration`
- Link: `bil_registration.extraction_id` → `extraction.id`
- API contract alignment: the server returns this attempt id as `registration_id`

### Service Layer

Key interfaces and implementations:

- `src/services/core/extraction/IBilService.ts`
- `src/services/core/extraction/impl/BilService.ts`
- `src/services/core/extraction/repository/IBilRegistrationRepository.ts`
- `src/services/core/extraction/repository/SupabaseBilRegistrationRepository.ts`

The core operations are:

- List attempts for a single extraction version id
- List attempts for many extraction version ids (used to cover the full extraction version history)

### UI Integration

The detail view uses a hook to load and group attempts by extraction version id:

- `src/pages/extractions/useBilRegistrationState.ts`

It fetches attempts via `services.bilService.listRegistrationsByExtractionIds(...)`, groups by `extraction_id`, and exposes:

- latest successful `certificateId`
- attempt list per extraction version
- selection state for the UI

---

## Interface-First Design

### Service Interface

Defines contract:

```typescript
// IBlogService.ts
export interface IBlogService {
  getAllBlogs(): BlogPost[];
  getBlogBySlug(slug: string): BlogPost | undefined;
  getBlogById(id: string, lang?: string): BlogPost | undefined;
}
```

### Repository Interface

Defines data access:

```typescript
// IBlogRepository.ts
export interface IBlogRepository {
  getAllBlogs(): BlogPost[];
  findBySlug(slug: string): BlogPost | undefined;
  findById(id: string, lang?: string): BlogPost | undefined;
}
```

---

## Implementation

### Repository Implementation

```typescript
// BlogRepository.ts
export class BlogRepository implements IBlogRepository {
  constructor(private readonly logger: ILogger) {}

  findAll(): BlogPost[] {
    // Data access (load files, parse)
    return ALL_POSTS;
  }

  findBySlug(slug: string): BlogPost | undefined {
    return ALL_POSTS.find(p => p.slug === slug);
  }
}
```

**Important:**
- No business logic
- Only data access
- Stateless

### Service Implementation

```typescript
// BlogService.ts
export class BlogService implements IBlogService {
  constructor(
    private readonly blogRepo: IBlogRepository,
    private readonly logger: ILogger
  ) {}

  getAllBlogs(): BlogPost[] {
    this.logger.debug('BlogService', 'Fetching all posts');
    return this.blogRepo.findAll();
  }

  getPostBySlug(slug: string): BlogPost | undefined {
    const post = this.blogRepo.findBySlug(slug);
    if (!post) {
      this.logger.warn('BlogService', 'Post not found', { slug });
    }
    return post;
  }
}
```

**Important:**
- Business logic (logging, validation)
- Uses repository via DI
- Stateless

---

## ServiceFactory Integration

### 1. ServiceContainer

Defines external dependencies:

```typescript
// factory/ServiceContainer.ts
export interface ServiceContainer {
  logger: ILogger;
}
```

### 2. ServiceFactory

Initializes services and repositories:

```typescript
// factory/ServiceFactory.ts
class ServiceFactory {
  private static instance: ServiceFactory;
  private readonly _blogService: IBlogService;

  private constructor(container: ServiceContainer) {
    // Create repository
    const blogRepo = new BlogRepository(container.logger);

    // Initialize service with repository
    this._blogService = new BlogService(blogRepo, container.logger);
  }

  static initialize(container: ServiceContainer): void {
    if (ServiceFactory.instance) return;
    ServiceFactory.instance = new ServiceFactory(container);
  }

  get blogService(): IBlogService {
    return this._blogService;
  }
}
```

### 3. Lazy Getters

Export for safe imports:

```typescript
export const serviceFactory = {
  get blogService() {
    return ServiceFactory.getInstance().blogService;
  }
};
```

---

## Initialization

### Application Startup (main.tsx)

```typescript
import { ServiceFactory } from '@/services/factory/ServiceFactory';
import { ConsoleLogger } from '@/services/infrastructure/logging/ConsoleLogger';

ServiceFactory.initialize({
  logger: new ConsoleLogger()
});
```

### Usage in Components

```typescript
import { serviceFactory } from '@/services/factory/ServiceFactory';

const post = serviceFactory.blogService.getPostBySlug(slug);
```

---

## Repository Pattern (even without DB)

**Why repository without database?**

✅ **Benefits:**
- Data access abstracted
- Swappable (later DB instead of files)
- Testable (mock repository)
- Clear separation

**Beacon uses files instead of DB:**
- Repository reads markdown files
- Repository parses frontmatter
- Service uses repository
- Later: Files → DB without changing service

**Example BlogRepository:**

```typescript
export class BlogRepository implements IBlogRepository {
  constructor(private readonly logger: ILogger) {}

  findAll(): BlogPost[] {
    // Currently: Files with import.meta.glob
    const posts = this.loadPostsFromFiles();
    return posts;
  }

  private loadPostsFromFiles(): BlogPost[] {
    // Implementation: Parse markdown, extract frontmatter
    // Later: Supabase query
  }
}
```

---

## Dependency Injection

**Rule:** All dependencies via constructor

```typescript
// ✅ CORRECT
class BlogService {
  constructor(
    private readonly blogRepo: IBlogRepository,  // ← Injected
    private readonly logger: ILogger              // ← Injected
  ) {}
}

// ❌ WRONG
class BlogService {
  private blogRepo = new BlogRepository();  // ← Created inside!
}
```

**Why:**
- Testable (mock injection)
- Flexible (different implementations)
- No hidden dependencies
