# TASKS.md — La Cuchara

> **How to use:** Work tasks in order, top to bottom. Never skip a task.
> Mark each task `[x]` immediately after completing it and committing.
> If a task is blocked, log it in `AGENT_STATUS.log` and stop.

---

## Phase 1 — Project Scaffold

- [x] **1.1 — Create full project folder and file structure**
  Create all folders and empty files (or minimal boilerplate) as defined in `context.md`.
  Includes: `frontend/`, `backend/`, root config files (`CLEANUP_PENDING.md`, `AGENT_STATUS.log`, `README.md`).

- [x] **1.2 — Configure frontend boilerplate**
  Initialize Next.js App Router project with TypeScript and Tailwind CSS.
  Configure `next.config.ts`, `tailwind.config.ts`, `tsconfig.json`.
  Create `frontend/.env.local.example` with all required placeholders.

- [x] **1.3 — Configure backend boilerplate**
  Set up FastAPI entry point in `backend/app/main.py` with CORS middleware configured for the frontend URL.
  Create `backend/requirements.txt` with: `fastapi`, `uvicorn`, `supabase`, `python-dotenv`, `pydantic`.
  Create `backend/.env.example` with all required placeholders.
  Create `backend/app/core/config.py` to load all environment variables.

---

## Phase 2 — Database Schema

- [x] **2.1 — Write Supabase SQL schema**
  Create `backend/supabase_schema.sql` with all `CREATE TABLE` statements for all 8 tables as defined in `context.md`.
  Include FK constraints, default values, and CHECK constraints (role, rating range).
  Add comments explaining each table's purpose.

---

## Phase 3 — Backend: Core & Auth

- [x] **3.1 — Supabase client and dependencies**
  Implement `backend/app/core/supabase.py`: initialize the Supabase client using env vars. Handle missing env vars gracefully with a descriptive error, do not crash on startup.
  Implement `backend/app/dependencies.py`: `get_current_user` function that extracts and verifies the JWT from the `Authorization` header via Supabase Auth. Returns 401 if invalid.

- [x] **3.2 — Pydantic schemas**
  Implement all schemas in `backend/app/models/schemas.py`:
  - `UserCreate`, `UserOut`
  - `RestaurantCreate`, `RestaurantOut`
  - `MenuCreate`, `MenuOut`
  - `MenuItemCreate`, `MenuItemOut`
  - `ImageOut`
  - `RatingCreate`, `RatingOut`
  - `LoginRequest`, `TokenResponse`, `SignupRequest`

- [x] **3.3 — Auth endpoint: POST /auth/signup**
  Implement in `backend/app/routers/auth.py`.
  Body: `{ email, password, role: "user" | "owner", restaurant_name?: str }`
  - Creates user in Supabase Auth
  - Inserts row in `users` table with correct role
  - If role is `owner`: creates a row in `restaurants` and links `restaurant_id` to the user
  - Returns: `{ user_id, email, role, access_token }`
  - Wrap all Supabase calls in try/except with descriptive errors

- [x] **3.4 — Auth endpoint: POST /auth/login**
  Implement in `backend/app/routers/auth.py`.
  Body: `{ email, password }`
  Authenticates via Supabase Auth.
  Returns: `{ access_token, user_id, role }`

- [x] **3.5 — Auth endpoints: POST /auth/logout and GET /auth/me**
  `POST /auth/logout`: invalidates session in Supabase Auth using the Bearer token.
  `GET /auth/me`: returns the authenticated user's profile from `users` table using `get_current_user` dependency.

- [x] **3.6 — Register all routers in main.py**
  Register `auth` router in `backend/app/main.py`.
  Verify the app starts without errors even when Supabase env vars are not set.

---

## Phase 4 — Frontend: Foundation

- [x] **4.1 — Supabase client and API lib**
  Implement `frontend/lib/supabaseClient.ts`: initialize Supabase JS client from env vars.
  Implement `frontend/lib/api.ts`: typed functions to call the FastAPI backend (`login`, `signup`, `logout`, `getMe`). Use `NEXT_PUBLIC_API_URL` as base URL.
  Implement `frontend/types/index.ts`: TypeScript types matching the Pydantic schemas (`User`, `Restaurant`, `TokenResponse`, etc.).

- [x] **4.2 — Layout, Navbar and ProtectedRoute**
  Implement `frontend/app/layout.tsx`: root layout with global styles.
  Implement `frontend/components/layout/Navbar.tsx`: shows app name "La Cuchara", navigation links, and logout button if authenticated.
  Implement `frontend/components/layout/ProtectedRoute.tsx`: HOC that checks for a valid token and required role. Redirects to `/login` if unauthenticated or unauthorized.

---

## Phase 5 — Frontend: Auth Pages

- [x] **5.1 — Login page**
  Implement `frontend/components/auth/LoginForm.tsx` and `frontend/app/login/page.tsx`.
  Fields: email, password.
  On submit: calls `POST /auth/login` via `api.ts`, stores `access_token`, redirects to `/dashboard` (role: `user`) or `/restaurant/upload` (role: `owner`).
  Shows inline validation errors and API error messages.

- [x] **5.2 — Signup page**
  Implement `frontend/components/auth/SignupForm.tsx` and `frontend/app/signup/page.tsx`.
  Role selector: "Usuario" / "Restaurante".
  Fields: email, password, confirm password. If "Restaurante": additional `restaurant_name` field appears.
  On submit: calls `POST /auth/signup` via `api.ts`, redirects based on role.
  Shows inline validation and API error messages.

---

## Phase 6 — Frontend: Protected Pages

- [x] **6.1 — User dashboard**
  Implement `frontend/app/dashboard/page.tsx`.
  Protected (role: `user`). Uses `ProtectedRoute`.
  Shows: Navbar, welcome message with user email, placeholder section for restaurant search (with a "Próximamente" message), logout button.

- [x] **6.2 — Restaurant menu upload page**
  Implement `frontend/components/restaurant/MenuUpload.tsx` and `frontend/app/restaurant/upload/page.tsx`.
  Protected (role: `owner`). Uses `ProtectedRoute`.
  Form fields: menu date, image file input, season_tag (optional text).
  On submit: calls `POST /menus/upload` (placeholder endpoint — show a success mock if endpoint doesn't exist yet).
  Shows loading state and success/error feedback.

---

## Phase 7 — Integration Check

- [x] **7.1 — End-to-end smoke test**
  Verify that:
  - Frontend builds without errors (`npm run build`)
  - Backend starts without errors (`uvicorn app.main:app`)
  - All `// TODO: conectar Supabase` and `# TODO: conectar Supabase` markers are present where expected
  - `.env.example` files are complete and accurate
  - `supabase_schema.sql` is valid SQL (no syntax errors)
  Document any remaining TODOs or known gaps in `AGENT_STATUS.log`.
