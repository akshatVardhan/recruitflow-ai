# RecruitFlow AI - Component Registry

# Maintained by: Frontend Dev
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

---

## Shared Components

(populated by Frontend Dev as components are built)

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
