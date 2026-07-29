# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

React + TypeScript + Vite frontend for "e-ombor" (a warehouse/inventory management system). UI strings and route names are largely in Uzbek (e.g. "Shartnomalar" = contracts, "Ombor" = warehouse).

## Commands

```bash
npm run dev        # start Vite dev server
npm run build       # tsc -b (project references) then vite build
npm run lint        # eslint .
npm run preview     # preview production build
```

There is no test runner configured in this project — do not assume Jest/Vitest exists.

Environment config lives in `.env` (`VITE_API_URL`), read via `import.meta.env`. The backend API is a separate service (Django-style REST — endpoints are trailing-slashed, e.g. `/warehouses/`, paginated list responses have `count`/`next`/`previous`/`results`).

## Architecture

### Layering: `api/` → `hooks/` → `pages/`

Each domain (warehouses, suppliers, contracts/`shartnomalar`, objects/`sites`) follows the same three-layer pattern:

1. **`src/api/<domain>.ts`** — plain async functions wrapping the shared `api` axios instance (`src/lib/axios.ts`). Also defines the TanStack Query key factory for that domain, e.g.:
   ```ts
   export const warehousesQueryKey = ["warehouses"] as const;
   export const warehouseQueryKey = (id: number) => [...warehousesQueryKey, id] as const;
   ```
2. **`src/hooks/use<Domain>.ts`** — TanStack Query hooks (`useQuery`/`useMutation`) built on top of the api functions. Mutations invalidate the list key and/or `setQueryData` the detail key on success. This is the only place react-query is called directly; pages consume these hooks, not the api layer.
3. **`src/pages/<domain>/`** — page components (list page, detail page, a `*Card` component, and often a `*Form` component for create/edit). Forms are plain controlled components with local `useState`, not `react-hook-form` (despite it being a dependency — it isn't actually used yet anywhere in `src`).

Types for each domain live in `src/types/<domain>.ts` (entity, `*Payload` for create/update bodies, and `*Response` for paginated list responses).

When adding a new domain/resource, replicate this exact structure rather than inventing a new pattern.

### Auth

- `src/stores/authStore.ts` — Zustand store (persisted to localStorage under `auth-storage`) holding `accessToken`, `refreshToken`, `user`.
- `src/lib/axios.ts` — shared axios instance. Request interceptor attaches `Authorization: Bearer <accessToken>`. Response interceptor handles 401s: deduplicates concurrent refresh calls via a module-level `refreshPromise`, retries the original request once after refresh, and force-logs-out (clearing the store, redirecting to `/`) if refresh fails or the refresh call itself 401s.
- `src/api/auth.ts` defines a *separate* unauthenticated axios instance (`authApi`) for `/auth/login/` and `/auth/refresh/` specifically, to avoid interceptor recursion.
- Route protection is done in `src/routs/router.tsx` via a `ProtectedRoute` wrapper that checks `accessToken` from the store and redirects to `/login` (client-side only — no route-level code splitting or loaders).

### Routing & layout

- Routes are defined in `src/routs/router.tsx` (note the misspelled directory name `routs`, not `routes`) using `createBrowserRouter`. All authenticated pages nest under a single `Layout` route.
- `src/layouts/Layout.tsx` composes `Sidebar` + `Header`/`Navbar`/`Footer` around an `<Outlet />`.

### Data fetching conventions

- `src/lib/queryClient.ts` sets global defaults: `retry: 1`, `staleTime: 5 min`, `refetchOnWindowFocus: false`.
- List hooks generally `select` the `.results` array out of the paginated response so pages work with plain arrays.
- Detail hooks (`use<Domain>(id)`) guard `enabled` on the id being a valid positive integer.

### Styling

Tailwind CSS v4 (via `@tailwindcss/vite` plugin, imported with `@import "tailwindcss"` in `src/index.css` — no `tailwind.config.js`). Styling is utility-class-first and inline; components are not broken into many small subcomponents — form/page components are often written as a single dense JSX expression rather than multi-line indented markup. Match this density when editing existing files rather than reformatting them.

Icons come from `lucide-react`. `antd` and `recharts` are dependencies but currently unused anywhere in `src` — check before assuming either is wired up.
