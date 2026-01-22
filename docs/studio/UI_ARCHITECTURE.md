# UI Architecture — xScanner Studio

Defines how UI components and pages are structured in xScanner Studio.

**Pattern:** React Router with shared Layout component

---

## Directory Structure

```
src/
├── pages/                 # Route components (content only)
│   └── DashboardPage.tsx
├── components/            # UI components
│   ├── Layout.tsx        # Header + Outlet + Footer wrapper
│   ├── Header.tsx        # Navigation, user menu, theme/language switchers
│   ├── Footer.tsx        # Copyright, links
│   ├── ErrorPage.tsx     # Error boundary
│   ├── LoginDialog.tsx   # Custom Auth UI (sign in/up)
│   └── messages/         # Global message rendering
│       ├── InfoPanel.tsx
│       └── MessageCenter.tsx
├── lib/                  # Utilities
│   ├── supabase.ts       # Supabase client
│   ├── i18n.ts           # i18next config
│   ├── errors.ts         # Error normalization (AppError)
│   └── logging.ts        # Logging abstraction
├── ui/                   # UI framework layer (cross-feature)
│   └── messages/         # UI messaging data + provider
└── locales/              # Translation files (de/en)
```

---

## Routing Architecture

### Router Setup

**Entry:** `App.tsx` creates router after auth check

```tsx
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout user={session.user} pageTitle={t('extraction.title')} />,
    errorElement: <ErrorPage />,
    children: [
      { index: true, element: <DashboardPage /> },
      // Add more routes here
    ],
  },
])
```

### Layout Component

**Purpose:** Wraps all authenticated pages with consistent Header and Footer

- Header receives `user` and `pageTitle` props
- `<Outlet />` renders the current route's page component
- Footer is static across all pages

**Structure:**
```tsx
<div className="app-layout">  {/* flex column, min-h-screen */}
  <Header />                  {/* Navigation */}
  <main className="content">  {/* Max-width container */}
    <Outlet />                {/* Current page */}
  </main>
  <Footer />                  {/* mt-auto pushes to bottom */}
</div>
```

### Context-Sensitive Back Navigation

**Goal:** Replace "Back" buttons with a consistent back-arrow left of the page title, and make navigation return to the previous in-app route.

**Building blocks (Studio):**
- `src/components/layout/PageHeader.tsx`: Standard page title row with optional back arrow (left) and optional right-side actions.
- `src/lib/router/NavigationHistoryProvider.tsx`: Tracks the previous in-app route.
- `src/lib/router/useContextSensitiveBack.ts`: Navigates to the tracked previous route, with a safe fallback.

**Wiring:** `NavigationHistoryProvider` is mounted in the authenticated layout so every page can use it.

**How to use in pages:**
```tsx
<PageHeader
  title={t('extraction.list.title')}
  subtitle={t('extraction.list.subtitle')}
  backLabel={t('common.action.back')}
  right={<button className="btn">{t('common.action.save')}</button>}
/>
```

**Notes:**
- Avoid hard-coded back destinations like `/` or `/extractions` in the UI. Prefer `PageHeader` (or `useContextSensitiveBack(...)`) so back behaves based on how the user arrived.
- The hook falls back to `navigate(-1)` when browser history exists, otherwise to the provided fallback path.

---

## Component Types

### 1. Pages (Route Components)

**Responsibilities:**
- Render page-specific content
- Call Supabase services via custom hooks
- No layout concerns (Header/Footer in Layout)

**Does NOT:**
- Render Header or Footer
- Handle routing logic
- Manage global state

**Example:**

```tsx
// pages/Blog.tsx
import { serviceFactory } from '@/services/factory/ServiceFactory';

const Blog = () => {
  const blogs = serviceFactory.blogService.getAllBlogs();

  return (
    <>
      <Header />
      <main>
        <PostList posts={posts} />
      </main>
      <Footer />
    </>
  );
};
```

**Key characteristics:**
- Simple, layout-focused
- Delegates to components
- Uses services directly or via hooks

#### Extraction Pages (real example)

xScanner Studio has two main pages for the extraction domain:

- `ExtractionsPage.tsx`: list view, filters, pagination, and overview state persistence.
- `ExtractionDetailPage.tsx`: detail view showing the active extraction version, full history, image preview, and BIL registration attempts.

**BIL registrations in the detail view:**

- The page loads the extraction version history via `services.extractionService`.
- It loads BIL registration attempts for all versions via `useBilRegistrationState` and renders them in `BilRegistrationPanel`.
- Attempts are grouped by extraction version id (`bil_registration.extraction_id` → `extraction.id`).

**Overview state persistence:**

- The list page persists state in `sessionStorage` (filters/pagination/scroll), so navigation back from detail view restores the overview.

---

### 2. Components (Reusable UI)

**Responsibilities:**
- Render UI
- Handle user events
- Receive data via props
- No data fetching

**Structure:**

```
components/
├── ui/                    # Base components (shadcn/ui)
│   ├── button.tsx
│   ├── card.tsx
│   └── badge.tsx
├── layout/                # Layout components
│   ├── Header.tsx
│   └── Footer.tsx
└── blog/                  # Feature-specific
    ├── PostList.tsx
    └── PostCard.tsx
```

**Example:**

```tsx
// components/blog/PostCard.tsx
interface PostCardProps {
  post: BlogPost;
  onClick?: () => void;
}

export const PostCard = ({ post, onClick }: PostCardProps) => {
  return (
    <Card onClick={onClick}>
      <CardHeader>
        <CardTitle>{post.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p>{post.excerpt}</p>
      </CardContent>
    </Card>
  );
};
```

**Key characteristics:**
- Dumb/Presentational
- Props-driven
- No side effects
- Highly reusable

---

### 3. Hooks (Custom Logic)

**Responsibilities:**
- Encapsulate React logic (useState, useEffect)
- Integrate with services
- Provide loading/error states
- Reusable across components

**When to create:**
- Logic used in multiple components
- Complex state management
- Service integration needs abstraction

**Example:**

```tsx
// hooks/useBlogPosts.ts
export const useBlogPosts = (preview: boolean = false) => {
  const [posts, setPosts] = useState<BlogPost[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const allBlogs = serviceFactory.blogService.getAllBlogs();
    const filtered = allBlogs.filter(p =>
      serviceFactory.blogService.isBlogVisible(p, preview)
    );
    setPosts(filtered);
    setLoading(false);
  }, [preview]);

  return { posts, loading };
};
```

**Usage in page:**

```tsx
const Blog = () => {
  const { posts, loading } = useBlogPosts();

  if (loading) return <Spinner />;
  return <PostList posts={posts} />;
};
```

---

## Routing Architecture

**Pattern:** Centralized route config with feature-based organization

### Structure

```
src/
├── Router.tsx              # Main router, combines all routes
├── routing/
│   ├── routes.ts          # Central export (links)
│   └── queryParams.ts     # URL/localStorage helpers
└── pages/
    └── {feature}/
        └── routes.tsx     # Feature routes + links
```

### Key Principles

**1. Feature-based Routes**
- Each feature defines own routes (`pages/{feature}/routes.tsx`)
- Routes and links live together
- Router imports and combines them

**2. Type-safe Links**
- Link builders for all routes
- No hardcoded URLs in components
- Centralized via `routes.{feature}.{action}()`

**3. Query Params + LocalStorage**
- Routing-wide flags (e.g., `preview`, `lang`)
- Persist across navigation
- Hash-safe URL manipulation

`preview` semantics:
- URL: `?preview=true|false` (explicit)
- Persist to localStorage only when explicit
- No legacy fallback for `showDrafts` query param

### Example

**Feature Routes:**
```tsx
// pages/blog/routes.tsx
export const blogRoutes = [
  <Route path="/:lang/blog" element={<Blog />} />,
  <Route path="/:lang/blog/:slug" element={<BlogPost />} />
];

export const blogLinks = {
  list: (lang: string) => `/${lang}/blog`,
  detail: (lang: string, slug: string) => `/${lang}/blog/${slug}`
};
```

**Central Router:**
```tsx
// Router.tsx
export function Router() {
  return (
    <Routes>
      <Route path="/" element={<Index />} />
      {blogRoutes.map((route, i) => <Route key={i} {...route} />)}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
```

**Usage:**
```tsx
import { routes } from '@/routing/routes';

// Type-safe navigation
<Link to={routes.blog.detail('en', 'my-post')}>Read Post</Link>
```

---

## Component Patterns

### Container/Presentation Pattern

**Separation:** Smart containers + Dumb components

**Container (Smart):**
- Fetches data
- Manages state
- Handles events
- Passes props to presentation

**Presentation (Dumb):**
- Renders UI
- Receives props
- Emits events
- No state (except UI state like hover)

---

## UI Messaging Pattern

xScanner Studio uses a small, consistent UI messaging framework to keep user-facing feedback predictable across features.

### Goals

- Standardize the UI for `info`, `success`, `warning`, and `error`
- Keep pages/hooks free from ad-hoc strings and one-off alert layouts
- Ensure message text is localizable (i18n-first)
- Keep the UI consistent for `info`, `success`, `warning`, and `error`

### Building Blocks

- `UiMessage` (data model)
  - Lives in `src/ui/messages/types.ts`
  - Represents a user-facing message (variant, title, description)
  - Created close to the source (page/hook/service adapter), not by presentational components

- `UiMessagesProvider` (state + API)
  - Lives in `src/ui/messages/UiMessagesProvider.tsx`
  - Provides `push()`, `dismiss()`, and `clear()`
  - Mounted in `App.tsx` so it works on login screen and authenticated routes

- `InfoPanel` (renderer)
  - Lives in `src/components/messages/InfoPanel.tsx`
  - Renders one message consistently, including a dismiss action

- `MessageCenter` (message list)
  - Lives in `src/components/messages/MessageCenter.tsx`
  - Renders the current queue of messages from context

### Responsibilities (separation)

- Pages/hooks decide *what happened* and push a `UiMessage`
- Components decide *how it looks* (`InfoPanel` renders the message)
- Feature-specific panels may compose `InfoPanel`, but should not introduce a second generic messaging framework

### Placement Rules

- Generic messaging components belong in `src/components/messages/`
- Messaging state + helpers belong in `src/ui/messages/`

**i18n note:** Studio runs strict "unused key" checks. Therefore, message text should be produced via centralized helpers that reference translation keys as string literals (example: `src/lib/errors.ts` uses a `switch` mapping). Avoid using fully dynamic `t(someVariableKey)` for new message keys.

### Do / Don't (short)

- Do: Create `UiMessage` close to the source and render it via `MessageCenter`
- Do: Convert exceptions into user-facing messages via `src/lib/errors.ts` + `src/ui/messages/fromError.ts`
- Don't: Add new one-off alert layouts (compose `InfoPanel` instead)
- Don't: Surface raw `error.message` to end users

**Example:**

```tsx
// Container
const BlogContainer = () => {
  const blogs = serviceFactory.blogService.getAllBlogs();
  const handlePostClick = (slug: string) => navigate(`/blog/${slug}`);

  return <PostList posts={posts} onPostClick={handlePostClick} />;
};

// Presentation
interface PostListProps {
  posts: BlogPost[];
  onPostClick: (slug: string) => void;
}

const PostList = ({ posts, onPostClick }: PostListProps) => {
  return (
    <div>
      {posts.map(post => (
        <PostCard
          key={post.slug}
          post={post}
          onClick={() => onPostClick(post.slug)}
        />
      ))}
    </div>
  );
};
```

---

### Service Integration

**Rule:** Pages and hooks integrate with services, components don't.

```tsx
// ✅ CORRECT - Page uses service
const Blog = () => {
  const blogs = serviceFactory.blogService.getAllBlogs();
  return <PostList posts={posts} />;
};

// ✅ CORRECT - Hook uses service
const useBlogPosts = () => {
  const blogs = serviceFactory.blogService.getAllBlogs();
  return posts;
};

// ❌ WRONG - Component uses service
const PostList = () => {
  const blogs = serviceFactory.blogService.getAllBlogs(); // NO!
  return <div>{/* ... */}</div>;
};
```

**Why:**
- Keeps components pure
- Easier to test
- Clearer data flow

---

### Props Patterns

**Interface-driven:**

```tsx
// ✅ CORRECT - Explicit interface
interface PostCardProps {
  post: BlogPost;
  onClick?: () => void;
  showMeta?: boolean;
}

const PostCard = ({ post, onClick, showMeta = true }: PostCardProps) => {
  // ...
};

// ❌ WRONG - No interface
const PostCard = (props: any) => {
  // ...
};
```

**Optional vs. Required:**

```tsx
interface PostCardProps {
  post: BlogPost;           // Required
  onClick?: () => void;     // Optional
  showMeta?: boolean;       // Optional with default
}

const PostCard = ({
  post,
  onClick,
  showMeta = true  // Default value
}: PostCardProps) => {
  // ...
};
```

---

## State Management

### Local State (useState)

**When:** Component-specific UI state

```tsx
const PostCard = ({ post }: PostCardProps) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <Card
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* ... */}
    </Card>
  );
};
```

### Lifted State

**When:** State shared between siblings

```tsx
const BlogPage = () => {
  const [preview, setPreview] = useState(false);

  return (
    <>
      <BlogFilter preview={preview} onChange={setPreview} />
      <BlogList preview={preview} />
    </>
  );
};
```

### URL State (useSearchParams)

**When:** State that should be shareable/bookmarkable

```tsx
const Blog = () => {
  const [searchParams] = useSearchParams();
  const preview = searchParams.get('preview') === 'true';

  const posts = serviceFactory.blogService.getAllBlogs()
    .filter(p => serviceFactory.blogService.isBlogVisible(p, preview));

  return <PostList posts={posts} />;
};
```

### Global State (Context)

**When:** App-wide state (auth, theme, i18n)

**Prefer:** URL params or props for data
**Use:** Context only for truly global concerns

---

## File Organization

### By Feature

```
components/
├── ui/              # Base components
├── layout/          # Layout components
├── blog/            # Blog-specific
│   ├── PostList.tsx
│   ├── PostCard.tsx
│   └── PostMeta.tsx
└── social/          # Social-specific
    ├── PostEditor.tsx
    └── PostPreview.tsx
```

### Naming Conventions

**Components:**
- PascalCase: `PostCard.tsx`, `BlogList.tsx`
- Descriptive: `PostCard` not `Card`

**Hooks:**
- camelCase with `use` prefix: `useBlogPosts.ts`
- Descriptive: `useBlogPosts` not `usePosts`

**Utilities:**
- camelCase: `formatDate.ts`, `parseMarkdown.ts`

---

## Component Size

**Maximum:** ~300 lines per file

**When to split:**
- Extract repeated JSX into components
- Extract complex logic into hooks
- Extract helper functions into utils

**Example:**

```tsx
// ❌ WRONG - Too large (600 lines)
const BlogPost = () => {
  // 100 lines of logic
  // 500 lines of JSX
};

// ✅ CORRECT - Split
const BlogPost = () => {
  const { post, loading } = useBlogPost(slug);

  return (
    <>
      <PostHeader post={post} />
      <PostContent content={post.content} />
      <PostMeta post={post} />
    </>
  );
};
```

---

## Styling Patterns

### Tailwind Utility Classes

**Prefer:** Tailwind utilities over custom CSS

```tsx
// ✅ CORRECT
<Card className="p-4 hover:bg-muted">
  <h2 className="text-2xl font-bold mb-2">{title}</h2>
</Card>

// ❌ WRONG - Custom CSS
<Card className="custom-card">
  <h2 className="custom-title">{title}</h2>
</Card>
```

### Component Variants (shadcn/ui)

**Use:** Built-in variants for consistency

```tsx
<Badge variant="outline">Draft</Badge>
<Badge variant="default">Published</Badge>
<Button variant="ghost">Cancel</Button>
```

### Conditional Styling

**Use:** `cn()` utility for conditional classes

```tsx
import { cn } from '@/lib/utils';

<Card className={cn(
  "p-4",
  isDraft && "border-dashed",
  isPublished && "bg-green-50"
)}>
```

---

## Best Practices

### Components

- ✅ Keep components focused (single responsibility)
- ✅ Use TypeScript interfaces for props
- ✅ Provide default values for optional props
- ✅ Extract repeated JSX into components
- ❌ No business logic in components
- ❌ No direct service calls in components
- ❌ No useState for data (use props)

### Pages

- ✅ Simple, layout-focused
- ✅ Delegate to components
- ✅ Use services via serviceFactory
- ✅ Use hooks for complex logic
- ❌ No complex JSX (extract to components)
- ❌ No business logic (use services)

### Hooks

- ✅ Encapsulate reusable logic
- ✅ Provide loading/error states
- ✅ Use services via serviceFactory
- ❌ Don't make hooks too generic
- ❌ Don't duplicate service logic

### File Size

- ✅ Max 300 lines per file
- ✅ Split large files into smaller ones
- ✅ Use barrel exports (index.ts)

---

## Anti-Patterns

### ❌ Business Logic in Components

```tsx
// ❌ WRONG
const PostCard = ({ post }: PostCardProps) => {
  // Business logic in component!
  const isVisible = post.status === 'published' &&
                    new Date(post.date) <= new Date();

  if (!isVisible) return null;
  return <Card>{post.title}</Card>;
};

// ✅ CORRECT
const PostCard = ({ post }: PostCardProps) => {
  return <Card>{post.title}</Card>;
};

// Logic in service
const visiblePosts = posts.filter(p =>
  blogService.isBlogVisible(p, preview)
);
```

### ❌ Direct Service Calls in Components

```tsx
// ❌ WRONG
const PostList = () => {
  const blogs = serviceFactory.blogService.getAllBlogs(); // NO!
  return <div>{/* ... */}</div>;
};

// ✅ CORRECT
const BlogPage = () => {
  const blogs = serviceFactory.blogService.getAllBlogs(); // YES!
  return <PostList posts={posts} />;
};
```

### ❌ Props Drilling

```tsx
// ❌ WRONG - Drilling through many levels
<Parent>
  <Child1 preview={preview}>
    <Child2 preview={preview}>
      <Child3 preview={preview} />
    </Child2>
  </Child1>
</Parent>

// ✅ CORRECT - Use Context or lift state
const PreviewContext = createContext<boolean>(false);

<PreviewProvider value={preview}>
  <Parent>
    <Child1>
      <Child2>
        <Child3 />
      </Child2>
    </Child1>
  </Parent>
</PreviewProvider>
```
