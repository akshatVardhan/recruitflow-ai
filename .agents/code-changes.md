# RecruitFlow AI - Code Changes Log

## 2026-07-01 - RF-18 - Next.js 14.x to 16.x upgrade
- **Branch:** feature/RF-18-upgrade-nextjs
- **Scope:** Frontend framework upgrade
- **Files changed:**
  - `frontend/package.json` - bumped all dependencies (next@16.2.9, react@19.2.7, eslint@9, eslint-config-next@16.2.9, etc.)
  - `frontend/next.config.mjs` - added `output: "standalone"` and `reactStrictMode: true`
  - `frontend/eslint.config.mjs` - created new ESLint flat config for ESLint 9
  - `frontend/.eslintrc.json` - deleted (replaced by flat config)
  - `frontend/tsconfig.json` - auto-updated by Next.js 16 build (jsx: react-jsx, added .next/dev/types)
  - `frontend/package-lock.json` - regenerated
  - `frontend/next-env.d.ts` - auto-updated by Next.js 16
