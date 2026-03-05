# Getting Started & Testing Guide — La Cuchara

> This guide covers **everything you need** to set up the project from scratch after cloning the repository.

---

## 1. Prerequisites — Install These First

| Tool | Version | Download | Notes |
|---|---|---|---|
| **Node.js** | v18+ | [nodejs.org](https://nodejs.org) | Choose the LTS version |
| **Python** | 3.11+ | [python.org](https://python.org) | On Windows use `py` instead of `python` |
| **Microsoft C++ Build Tools** | 14.0+ | [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/) | Required for the `supabase` Python package. During installation, select **"Desarrollo para el escritorio con C++"** |
| **Git** | Any | [git-scm.com](https://git-scm.com) | Already installed if you cloned the repo |

### Verify installations

Open a terminal and run:

```powershell
node --version    # Should show v18.x or higher
py --version      # Should show Python 3.11+
git --version     # Should show git version X.X
```

---

## 2. Clone the Repository

```powershell
git clone https://github.com/JorgePulgar/La-Cuchara.git
cd La-Cuchara
git checkout dev
```

---

## 3. Supabase — Get the API Keys

The Supabase project is already configured (database tables created, email confirmation disabled). You just need the API keys.

1. Log in to [supabase.com](https://supabase.com) and open the shared project.
2. Go to **Project Settings** → **API**.
3. Copy these three values:
   - **Project URL** (e.g. `https://xxxxx.supabase.co`)
   - **anon public key** (starts with `eyJ...`)
   - **service_role key** (starts with `eyJ...`) — keep this secret!

---

## 4. Configure Environment Variables

### Backend

```powershell
cd backend
copy .env.example .env
```

Edit `backend/.env` with your real Supabase values:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
FRONTEND_URL=http://localhost:3000
```

### Frontend

```powershell
cd frontend
copy .env.local.example .env.local
```

Edit `frontend/.env.local`:

```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> ⚠️ **Never commit `.env` or `.env.local` files** — they contain secrets and are already in `.gitignore`.

---

## 5. Install Dependencies

### Backend (Python)

```powershell
cd backend
py -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend (Node.js)

```powershell
cd frontend
npm install
```

---

## 6. Run the Application

You need **two terminals** open at the same time:

### Terminal 1 — Backend

```powershell
cd backend
.\venv\Scripts\activate
py -m uvicorn app.main:app --reload
```

✅ You should see: `Uvicorn running on http://127.0.0.1:8000`

**Quick check:** Open http://localhost:8000 — you should see:

```json
{"message": "La Cuchara API is running", "status": "ok"}
```

**API Docs:** http://localhost:8000/docs (interactive Swagger UI)

### Terminal 2 — Frontend

```powershell
cd frontend
npm run dev
```

✅ You should see: `Ready on http://localhost:3000`

**Open http://localhost:3000** in your browser to see the app.

---

## 7. Test the Application

### 7.1 — Home Page (`/`)

- Open http://localhost:3000
- You should see the "La Cuchara" heading
- Navbar shows "Iniciar sesión" and "Crear cuenta"

### 7.2 — Sign Up (`/signup`)

- Click "Crear cuenta" in the navbar
- Choose a role: **👤 Usuario** or **🍽️ Restaurante**
- If "Restaurante" is selected, a restaurant name field appears
- Fill in your data and submit
- On success → redirects to `/dashboard` (user) or `/restaurant/upload` (owner)

**Client-side validation tests:**
- Empty form → "El email es obligatorio"
- Short password → "La contraseña debe tener al menos 6 caracteres"
- Mismatched passwords → "Las contraseñas no coinciden"

### 7.3 — Log In (`/login`)

- Click "Iniciar sesión" in the navbar
- Enter the credentials you just created
- On success → redirects based on role

### 7.4 — Dashboard (`/dashboard`)

- **Requires login** (role: `user`)
- Shows welcome message with your email
- Restaurant search section with a "Próximamente" placeholder

### 7.5 — Menu Upload (`/restaurant/upload`)

- **Requires login** (role: `owner`)
- Form with: date picker, image upload, season tag (optional)
- Submit → shows success message (mock — upload endpoint not yet implemented)

### 7.6 — Log Out

- Click "Cerrar sesión" in the navbar → clears session, redirects to `/login`

---

## 8. Test Backend API Directly (Optional)

Use the **Swagger UI** at http://localhost:8000/docs:

### POST /auth/signup
```json
{
  "email": "test@example.com",
  "password": "password123",
  "role": "user"
}
```

### POST /auth/login
```json
{
  "email": "test@example.com",
  "password": "password123"
}
```

### GET /auth/me
- Click "Authorize" in Swagger UI
- Paste the `access_token` from the login response
- Execute → should return user profile

### POST /auth/logout
- Uses the same Bearer token
- Should return `{"message": "Logged out successfully"}`

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `python` not found | Use `py` instead of `python` on Windows |
| `pip install` fails with "Microsoft Visual C++ 14.0 required" | Install [C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) → select "Desarrollo para el escritorio con C++" → restart |
| `uvicorn` not found after pip install | Use `py -m uvicorn app.main:app --reload` instead |
| Backend crashes on startup | Check that `backend/.env` exists with valid Supabase values |
| "Supabase not connected" error | Fill in real Supabase credentials in `.env` files |
| "Failed to fetch" on login/signup | Make sure the backend is running on port 8000 |
| "Email not confirmed" on login | Disable email confirmation in Supabase dashboard (see section 3.2) |
| Frontend pages redirect to login | You need to be logged in with the correct role |
| `npm run dev` fails | Make sure you run it from the `frontend/` directory, not the project root |

---

## Testing Without Supabase

If Supabase is not set up yet:

- **Frontend** pages will load and display correctly
- **Login/Signup forms** will show client-side validation
- **API calls** will fail with "Supabase not connected" errors (expected)
- **Menu upload** will show a mock success message
- **Protected pages** will redirect to `/login`
