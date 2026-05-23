# PTAA Web

Next.js 14 (App Router) dashboard for Personal Tracking AI Assistant.

## Local development

```bash
cp .env.example .env.local
npm install
npm run dev
```

Open <http://localhost:3000>.

## Pages

| Route | Description |
|-------|-------------|
| `/`           | Marketing landing |
| `/login`      | Sign in |
| `/signup`     | Create account |
| `/dashboard`  | KPIs + charts (productivity, focus, top apps, heatmap) |
| `/coding`     | Coding analytics — languages, projects |
| `/apps`       | App usage table + classification |
| `/insights`   | AI-generated insights & alerts |
| `/chat`       | AI chat assistant grounded on your data |
| `/settings`   | Profile + connected devices |

## Stack

- **Next.js 14** — App Router, server components where useful
- **TypeScript** — strict mode
- **TailwindCSS** + **ShadCN-style** primitives + Radix UI
- **TanStack Query** — server state, automatic refetch & cache
- **Zustand** — auth tokens (localStorage, partialized)
- **Recharts** — charts (custom themed)
- **Framer Motion** — micro-animations
- **Sonner** — toasts
- **Zod** + **react-hook-form** — auth form validation

## Auth flow

- `useAuthStore` persists access + refresh tokens in localStorage.
- The shared `api` client transparently refreshes on 401 (single in-flight
  promise ensures no thundering herd).
- `<AuthGuard>` (in `(app)/layout.tsx`) gates protected routes client-side.
