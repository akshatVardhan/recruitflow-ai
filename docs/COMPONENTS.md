# RecruitFlow AI - Component Registry

# Maintained by: Implementer (2026-07-11: Frontend Dev merged into
# Implementer in a role consolidation)
# Updated whenever a new reusable component is created or an existing one changes.
# Purpose: prevents duplicate components being built across features.
# Before building any new component, check if one already exists here.
# For architectural patterns and decisions (not individual component reference), see docs/ADR.md instead.

---

## How to Read This File

Each entry covers:
- Location: file path relative to frontend/
- Used in: which pages or features use this component
- Props: key props the component accepts
- Notes: anything non-obvious about usage or behaviour

---

## Shell Components

### AppShell
Location: app/(dashboard)/layout.tsx
Used in: all dashboard pages
Notes: renders persistent sidebar and top bar, wraps all authenticated routes

### Sidebar
Location: components/shared/sidebar.tsx
Used in: AppShell
Notes: collapsible on desktop (w-64 open, w-16 collapsed), Sheet on mobile
       active link uses blue-600/10 background with right border

### TopBar
Location: components/shared/top-bar.tsx
Used in: AppShell
Notes: always shows active client name, user menu on right
       client name comes from useActiveClient hook
       STALE as of 2026-07-10: no useActiveClient hook exists anywhere
       in the codebase (verified via grep) - this note predates
       PR #64's real tenancy model (see docs/ADR.md ADR-009), where
       client_id is passed per-request rather than held as one "active"
       client. Needs a real fix, not touched here to keep this entry's
       scope to what PR #64 actually added.

---

## Auth (added by PR #64, RF-CONTRACT-1 / RF-63)

### LoginPage
Location: app/(auth)/login/page.tsx
Used in: /login route
Notes: plain email/password form, calls useAuth().login, redirects to
       /doc-studio on success. No "remember me" or OAuth, email+password only.

### RegisterPage
Location: app/(auth)/register/page.tsx
Used in: /register route
Notes: calls lib/api/auth.ts's registerUser directly (not through
       useAuth) then presumably redirects to /login - registration
       doesn't auto-login.

### useAuth
Location: hooks/use-auth.ts
Used in: LoginPage (RegisterPage calls the API function directly instead)
Returns: { user, isLoading, error, login, ... } - login() posts to
         /api/v1/auth/login, stores the access token via
         lib/api's setAccessToken, sets user state from the response.
Notes: No client-selection concept here - see ADR-009, tenancy is
       per-request client_id, not a hook-level "active client."

### lib/api/auth.ts, lib/api/clients.ts
Location: lib/api/auth.ts, lib/api/clients.ts
Used in: RegisterPage (auth.ts), any client-scoped page (clients.ts)
Notes: thin fetch wrappers over the shared axios instance in lib/api.ts
       (which holds the access token / attaches the Bearer header).
       clients.ts exposes listClients/createClient against
       /api/v1/clients - no update/delete yet, matches the backend's
       current CRUD surface (create+list only as of PR #64).

There is no separate "client-selector" component - client selection
happens inline wherever a client_id is needed (e.g. the doc upload
form), not via a shared reusable picker. If one gets built later, add
it here.

---

## Shared Components

(populated by Implementer as components are built)

### Example entry format:

### ComponentName
Location: components/shared/component-name.tsx
Used in: Doc Studio, Document Management
Props:
  - propName: type - description
  - propName: type - description
Notes: any non-obvious usage details

---

## Feature Components

### Doc Studio
(populated as Doc Studio is built)

### ATS
(populated as ATS is built)

### Document Management
(populated as Document Management is built)

### Talent Finder
(populated as Talent Finder is built)

### Job Finder
(populated as Job Finder is built)

### AI Chat
(populated as AI Chat is built)
