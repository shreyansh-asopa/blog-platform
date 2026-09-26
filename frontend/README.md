# Frontend

The Lumen web app: React + TypeScript, built with Vite. Runs on `http://localhost:5173`.

## Running it

The API must be running first (`docker compose up -d` from the repo root). Then:

```sh
cd frontend
npm install      # once, and whenever package.json changes
npm run dev      # http://localhost:5173, reloads as you edit
```

The dev server forwards `/api` and `/uploads` to the API on port 8000 (see `vite.config.ts`),
so the browser only ever talks to one address. Set `VITE_API_PROXY` to point it elsewhere.

## Checks

The same checks run in CI on every pull request:

```sh
npm run typecheck      # TypeScript
npm run lint           # oxlint
npm run format:check   # Prettier (npm run format fixes it)
npm run build          # production build into dist/
```

## How it's organised

- `src/api/`: the only code that calls the API. `client.ts` adds the login token and turns
  error responses into an `ApiError`; `endpoints.ts` lists the calls; `types.ts` mirrors the
  backend schemas.
- `src/auth/`: who is logged in. The token is kept in `localStorage`; the user and their role
  are always fetched from `/users/me`, so a role change shows up without logging in again.
- `src/theme/` and `src/styles/global.css`: light and dark themes. Colours are CSS variables;
  "System" follows the OS setting, and the toggle in the top bar overrides it.
- `src/components/`: shared pieces (layout, post card, avatar, error message).
- `src/pages/`: one component per page. Each has its own `.module.css`, whose class names
  can't clash with other pages.

Data fetching uses TanStack Query, which caches responses and handles loading and error states.
