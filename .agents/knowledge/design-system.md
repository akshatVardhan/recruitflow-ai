# RecruitFlow AI - Design System

# Read by: Frontend Developer before building any component or page.
# This file defines all UI decisions for the project.
# Do not deviate from these rules without updating this file and noting the reason.

---

## Guiding Principles

1. Clarity over decoration - every element must have an obvious purpose
2. Content density over whitespace - this is a productivity tool, not a marketing page
3. Sidebar-first navigation - all features accessible from a persistent left sidebar
4. Consistent states - every component must handle empty, loading, and error states
5. Progressive disclosure - advanced filters and options are hidden until needed

---

## Tailwind Configuration

Extend the default Tailwind config with these custom values in tailwind.config.ts.

Colors (use these names in all components, never raw hex values):

Primary: blue-600 (interactive elements, primary buttons, active states)
Primary hover: blue-700
Primary text on primary: white

Neutral background: zinc-950 (page background)
Surface: zinc-900 (cards, panels, sidebar)
Surface elevated: zinc-800 (dropdowns, modals, tooltips)
Border: zinc-700 (dividers, input borders)
Border subtle: zinc-800 (section separators)

Text primary: zinc-50
Text secondary: zinc-400
Text disabled: zinc-600
Text placeholder: zinc-500

Success: green-500
Warning: amber-500
Error: red-500
Info: blue-400

Status colors (for ATS pipeline stages and JIRA-style labels):
Backlog: zinc-500
In Progress: blue-500
In Testing: amber-500
In Review: blue-400
Done: green-500
Blocked: red-500
Cancelled: zinc-600

---

## Typography

Font: Inter (Next.js Google Fonts import)
Fallback: system-ui, -apple-system, sans-serif

Scale (use Tailwind classes, not custom sizes):
- Page title: text-2xl font-semibold
- Section heading: text-lg font-medium
- Card title: text-base font-medium
- Body: text-sm
- Label: text-xs font-medium tracking-wide uppercase
- Caption / helper: text-xs text-zinc-400

---

## Spacing

Use the Tailwind default spacing scale.
Common patterns:
- Page padding: p-6
- Card padding: p-4
- Section gap: gap-6
- Item gap within section: gap-3
- Input label to input: gap-1.5
- Sidebar item padding: px-3 py-2

---

## Component Rules

### Sidebar
- Width: w-64 (open), w-16 (collapsed, icon-only)
- Background: bg-zinc-900
- Active link: bg-blue-600/10 text-blue-400 border-r-2 border-blue-600
- Inactive link: text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800
- Top: logo and project name
- Bottom: user avatar and client/workspace switcher
- On mobile: renders as a Sheet (shadcn/ui), triggered by hamburger button in top bar

### Top Bar
- Height: h-14
- Background: bg-zinc-900 border-b border-zinc-800
- Always shows: active client/workspace name (left), user menu (right)
- Never empty - always shows context

### Cards
- Background: bg-zinc-900
- Border: border border-zinc-800
- Radius: rounded-lg
- Padding: p-4
- Shadow: shadow-sm

### Buttons
Use shadcn/ui Button component with these variants:
- Primary action: variant="default" (blue-600 bg)
- Secondary / cancel: variant="outline"
- Destructive: variant="destructive"
- Ghost / subtle: variant="ghost"
- Size: default for most, sm for compact table actions, lg for empty state CTAs

### Inputs
Use shadcn/ui Input component.
All inputs must have an associated Label component.
Show error message below input using text-red-400 text-xs when validation fails.
Placeholder text must be descriptive (not "Enter value").

### Tables and Lists
- Use shadcn/ui Table for structured data
- Alternating row background: even rows bg-zinc-800/30
- Column headers: text-xs font-medium uppercase text-zinc-400
- Row hover: hover:bg-zinc-800/50
- Sticky header on scroll for tables taller than 400px

### Skeleton Loaders
Use skeleton loaders (pulsing gray bars) for all list and table loading states.
Never use a spinner as the only loading indicator for content areas.
Spinner is acceptable for button loading states only.

### Empty States
Every list, table, and search result must have a designed empty state.
Empty state must include:
- A short title describing what is empty ("No resumes yet")
- A brief explanation or next step ("Upload a resume to get started")
- A CTA button linking to the relevant action

### Forms
Use React Hook Form with Zod schema validation.
Show validation errors inline below each field, not in a toast.
Disable the submit button while the form is submitting.
Show a success toast after successful submission.
Clear form fields after successful submission unless editing an existing record.

### Toasts
Use shadcn/ui Sonner for all toast notifications.
- Success: green-500 left border
- Error: red-500 left border
- Info: blue-400 left border
- Duration: 4 seconds default, 8 seconds for error toasts
- Position: bottom-right

### Modals and Drawers
Use shadcn/ui Dialog for confirmation modals (delete, cancel actions).
Use shadcn/ui Sheet from the right for detail panels (candidate detail, document preview).
Do not use full-page modals.

---

## Feature-Specific Rules

### Doc Studio
- Reference file upload zone: full-width dashed border, drag-and-drop enabled
- Generation output: resizable text area with word count
- Step indicator during generation: "Searching references > Building context > Generating"
- Export buttons: always visible when output exists, not behind a dropdown

### ATS Kanban Board
- Column width: fixed 280px, horizontal scroll for many columns
- Card: white text on bg-zinc-800, candidate name bold, role and company text-zinc-400
- Drag active: card gets shadow-xl and slight scale-105
- Column count badge: shows count of cards in each column header
- Do not show archived or cancelled candidates on the board by default

### Document Management
- Default view: grid of cards (4 columns desktop, 2 tablet, 1 mobile)
- Each card: file type icon, document title, date, tag pills
- Tag pills: bg-zinc-700 text-zinc-300 text-xs rounded-full px-2 py-0.5
- Search bar: always visible at the top, searches name + tags + content
- Filter panel: collapsible, appears to the right on desktop, drawer on mobile

### AI Chat Interface
- Messages: user messages right-aligned bg-blue-600/20, assistant messages left-aligned bg-zinc-800
- Streaming token appearance: no typing indicator needed, text just appears progressively
- Message input: fixed at bottom, multiline, sends on Enter (Shift+Enter for newline)
- Show referenced documents below assistant messages as small pills when RAG retrieval is used

---

## Responsive Breakpoints

375px: mobile - single column, sidebar as drawer
768px: tablet - two columns where applicable, sidebar collapsible
1280px: desktop - full layout with persistent sidebar

Always design for 1280px first in components, then ensure 768px and 375px work.

---

## Accessibility

All interactive elements must have:
- Visible focus ring (Tailwind: focus-visible:ring-2 focus-visible:ring-blue-500)
- ARIA label if the element has no visible text label
- Keyboard navigation support (Enter and Space for buttons, Arrow keys for menus)

Color contrast: all text must meet WCAG AA (4.5:1 for normal text, 3:1 for large text).
Do not rely on color alone to convey status - always include text or an icon.
