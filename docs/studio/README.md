# Studio Documentation Index

Frontend documentation for **xScanner Studio** - the admin UI for bullion extraction management.

## Architecture

- [UI_ARCHITECTURE.md](UI_ARCHITECTURE.md) – Component structure, routing, authentication flow
- [SERVICE_ARCHITECTURE.md](SERVICE_ARCHITECTURE.md) – Supabase integration, API client, data layer
- [ADR-0001-frontend-server-persistence-boundary.md](ADR-0001-frontend-server-persistence-boundary.md) – Decision: server-only persistence ownership
- [MIGRATION_VARIANT_B_SERVER_OWNS_PERSISTENCE.md](MIGRATION_VARIANT_B_SERVER_OWNS_PERSISTENCE.md) – Incremental migration roadmap to Variant B
- [DESIGN_SYSTEM.md](DESIGN_SYSTEM.md) – Brand colors, CSS classes, component patterns

## Development

- [LOGGING.md](LOGGING.md) – Logger abstraction, structured logging, best practices
- [TESTING.md](TESTING.md) – Test strategy, Vitest setup, component testing
- [I18N.md](I18N.md) – Internationalization with i18next, scoped translations
- [PRE_COMMIT.md](PRE_COMMIT.md) – Pre-commit hooks, code quality automation

## Tech Stack

- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite 7
- **Styling**: Tailwind CSS 3.3
- **UI Components**: Custom components based on xApp design system
- **Backend**: Supabase (Auth + PostgreSQL + Storage)
- **API Integration**: FastAPI server on port 8010

## Key Concepts

### Brand Colors (xApp Design System)
- **Primary Gold**: `#C4A053`
- **Success Green**: `#5CB85C`
- **Warning Orange**: `#F39C12`
- **Error Red**: `#FF3B30`

### CSS Architecture
All component styles are defined in `/src/index.css` using:
- Custom CSS properties for colors (RGB format)
- `@layer components` for reusable classes
- Glassmorphism, gradients, animations

### Authentication Flow
1. User lands on Login page (Supabase Auth UI)
2. After login → Dashboard with persistent Layout (Header + Footer)
3. Navigation via React Router (client-side routing)
4. Logout clears session and returns to Login

### UI Structure
- **Layout Component**: Wraps all authenticated pages with Header and Footer
- **Pages**: Rendered in Layout's main content area
- **Error Page**: Catches routing errors and displays user-friendly message

### Data Layer
- **Supabase Client**: `/src/lib/supabase.ts`
- **Database**: `extraction` table with bitemporal versioning (`is_active` flag)
- **Database**: `bil_registration` table for BIL registration attempts (linked to `extraction.id`)
- **Storage**: `extractions` bucket for bullion images
- **Migrations**: `/supabase/migrations/`

**Versioning rule (audit trail):** UI corrections create a new row (new `id`) with the same `original_id` and set the previous active row to `is_active=false`.

## File Structure

```
repo/
├── src/
│   ├── components/        # React components
│   │   ├── Header.tsx     # App header with navigation
│   │   ├── Footer.tsx     # App footer
│   │   ├── Layout.tsx     # Wrapper for all pages
│   │   ├── LoginDialog.tsx
│   │   └── ErrorPage.tsx  # Error boundary page
│   ├── pages/             # Route components
│   │   ├── DashboardPage.tsx
│   │   ├── ExtractionsPage.tsx
│   │   └── ExtractionDetailPage.tsx
│   ├── lib/               # Utilities
│   │   └── supabase.ts    # Supabase client
│   ├── App.tsx            # Router setup + auth
│   ├── index.css          # Component classes + styling
│   └── main.tsx           # Entry point
├── vite.config.ts         # Vite config (port 8084)
├── tailwind.config.js     # Tailwind config (brand colors)
└── package.json           # Dependencies
```

## Development Workflow

### Start Studio
```bash
make start-studio          # Start Vite dev server on :8084
```

### With All Services
```bash
make start-all             # Starts Supabase and Studio
```

### Environment Variables
- `VITE_SUPABASE_URL` - Supabase API URL (http://localhost:56321)
- `VITE_SUPABASE_ANON_KEY` - Supabase anonymous key
- `VITE_API_URL` - FastAPI server URL (http://localhost:8010)
- `VITE_SUPABASE_STORAGE_BUCKET` - Optional. Storage bucket name (default: `extractions`)

See `/.env.local` for configuration.

## Next Steps

1. ✅ Authentication & Welcome Page
2. ✅ Extraction List View (active rows)
3. ✅ Extraction Detail/Edit View (creates new DB row per correction)
4. 🔄 Image Upload to Supabase Storage (UI-driven uploads)
5. 🔄 FastAPI Integration (start new extraction from Studio)
