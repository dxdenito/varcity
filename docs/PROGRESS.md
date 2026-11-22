\# VARCITY: PROJECT HANDOFF (read this fully before replying)



You are continuing as Technical Lead, Software Architect and Lead Full-Stack Developer for \*\*Varcity\*\*, an installable, modular University ERP and institutional identity platform for Kenyan universities. I am the product owner. The full original brief (stack, non-negotiables, phases) is in the project documents/memory; follow it.



\## First actions

1\. \*\*Read your saved memory file `/areas/varcity.md` before anything else.\*\* It holds my business rules (registration numbers, curriculum, grading, cohorts, calendar, mature entry, org structure, UI preferences) and my working preferences.

2\. Do \*\*not\*\* start Step 22 yet. \*\*Ask me clarifying questions first\*\* (see "Step 22" below), wait for my answers, then propose a short design for my approval before any code.

3\. Working style (also in memory): small steps, backend first then frontend, wait for my confirmation after each step, Windows + Command Prompt + VS Code commands in copy-paste blocks, full file when replacing a file (small edits for tiny changes), \*\*minimal code comments\*\*, challenge my decisions when you see a better way. Count tests from my pytest output, never from prediction.



\## Environment

\- Windows, project root `C:\\Users\\SA\\Desktop\\reactjs\\varcity` (not in OneDrive), git + GitHub (private repo), VS Code, Command Prompt.

\- Python 3.14.6, Node 24, npm 11, PostgreSQL 18 (local). \*\*No Docker yet (planned for the end), no Redis yet (dropped until the end).\*\*

\- Two terminals: backend `cd backend`, `.venv\\Scripts\\activate`, `uvicorn app.main:app --reload`; frontend `cd frontend`, `npm run dev` (http://localhost:5173, Vite proxies `/api` to http://127.0.0.1:8000).

\- Databases: `varcity` (dev) and `varcity\_test` (tests rebuild it from migrations each run; the test guard requires the name to end in `\_test`). DB role `varcity\_app`.

\- `backend/.env` (never committed; `.env.example` is): `VARCITY\_DATABASE\_URL`, `VARCITY\_TEST\_DATABASE\_URL`, `VARCITY\_SECRET\_KEY` (32+ chars). Optional: `VARCITY\_COOKIE\_SECURE` (must be true in production), `VARCITY\_SESSION\_IDLE\_MINUTES` (30), `VARCITY\_SESSION\_ABSOLUTE\_HOURS` (12).

\- Reset dev DB to see first-run setup again: `alembic downgrade base` then `alembic upgrade head` (wipes dev data).

\- Packages. Backend: fastapi, uvicorn, pydantic-settings, pydantic\[email], sqlalchemy (sync), psycopg\[binary], alembic, pwdlib\[argon2], python-multipart, tzdata, openpyxl, fpdf2, pytest, httpx2. Frontend: react, react-dom, react-router-dom, tailwindcss + @tailwindcss/vite (Tailwind v4), lucide-react. JavaScript, not TypeScript. \*\*Every file that contains JSX must end in `.jsx`.\*\*

\- Status: \*\*Steps 1-21 done and working. 76 pytest tests passing.\*\* Everything committed except docs/PROGRESS.md (this file).



\## Architecture in force

\- Modular monolith, `backend/app/modules/<module>/` with models, schemas, service, router. \*\*One PostgreSQL schema per module.\*\* Sync SQLAlchemy 2.x + psycopg 3. UUIDv7 primary keys (`uuid.uuid7()` via `core/ids.new\_id`).

\- Services never commit; routers commit/rollback. Audit rows are written with `audit.record(db, ...)` \*\*in the same transaction\*\* as the change. Audit log: partitioned monthly, append-only (trigger), secrets redacted. \*\*The migration created partitions for 24 months from Nov 2026; a background job must create future partitions before \~Oct 2028 (no job runner exists yet).\*\*

\- Auth: server-side sessions in `iam.user\_session` (only the SHA-256 of the token is stored), HttpOnly SameSite=Lax cookie `varcity\_session`, CSRF token = HMAC of the session token, sent as `X-CSRF-Token` on non-GET requests (frontend keeps it in memory; obtained from login and `/auth/me`). Argon2id passwords, min length 10. Lockout: 5 failures -> 15 minutes (super admin can unlock via API). Generic 401 messages. Timing equalisation for unknown emails.

\- \*\*Temporary design debt:\*\* authorization uses `is\_superuser` on `iam.user\_account` (`require\_superuser` dependency); RBAC phase replaces it with roles, permissions and org-scoped assignments. The initial admin is not linked to a person yet (directory comes later). Setup module creates the admin via iam models directly (to be moved behind a user-management service).

\- First-run setup: server prints a one-time \*\*setup code\*\* (HMAC of secret key) at startup while setup is pending; `/api/v1/setup/complete` creates branding + the first super admin in one transaction, can run only once.

\- Organization tree (`org` schema): configurable level types (`node\_type`, with allowed parents in `node\_type\_parent`) and `node` entries with a materialized `path` (text, `/id/id/`, prefix index). "Node" in code because "unit" means a taught unit. Codes are \*\*optional\*\*, uppercase, letters/digits only, unique per level, \*\*frozen once used\*\* (`code\_locked`). Delete is refused with reasons while dependents exist; move rewrites subtree paths; archive requires children archived first. Templates at initialize: College or Faculty chain (University > Campus > College/Faculty > School > Department; department allowed under school or college).

\- Settings (`settings` schema): `app\_setting` JSONB key/value (`branding` = university profile, `general` = timezone + date format) and `asset` (logo stored in DB, PNG/JPEG/WebP <= 512 KB, type detected from bytes). Public `/api/v1/public/branding` returns name, short name, motto, logo URL (versioned), colours (server-generated 50-950 palette + readable text colours), footer-credit flag, timezone, date format.

\- Bulk import/export engine: generic `core/tabular.py` (read CSV/XLSX, write CSV/XLSX/PDF, formula-injection safe, cp1252 CSV tolerated, 2 MB / 5000 rows) + `org/bulk.py` (columns Level, Name, Code, Parent path relative to the entry, Status on export; preview then all-or-nothing import; create-only, idempotent). PDF uses Latin-1 core font only (non-Latin prints `?`) until document templates arrive. Reuse this engine for programmes, staff, students.

\- Frontend: runtime theming via CSS variables from branding (`bg-brand-600`, `text-on-brand`, `bg-sidebar`, `text-on-sidebar`), `useBranding()` (has `refresh()`), `api()` helper in `lib/api.js` (cookies, CSRF, FormData, ApiError), React Router, `AuthProvider`/`useAuth`. UI rules I set: \*\*minimal modals, use full pages\*\* (drill-down pages with inline forms), compact dashboard-style density, white top bar, dark sidebar with Settings dropdown (Organization, General Settings), General Settings has tabs (University, Appearance, Regional), hamburger toggles sidebar collapse (remembered in localStorage), larger sidebar logo.



\## API surface (all under /api/v1)

\- health: GET `/health/live`, `/health/ready`

\- auth: POST `/auth/login`, GET `/auth/me`, POST `/auth/logout`; POST `/admin/users/{id}/unlock` (super admin)

\- setup: GET `/setup/status`, POST `/setup/complete`

\- public: GET `/public/branding`, `/public/branding/logo`

\- settings: GET/PUT `/settings/university`, POST/DELETE `/settings/university/logo`, GET/PUT `/settings/general`

\- org: GET `/org/node-types`, `/org/nodes`; POST `/org/initialize`, `/org/nodes`; PATCH/DELETE `/org/nodes/{id}`; POST `/org/nodes/{id}/move|archive|unarchive`; GET `/org/nodes/{id}/export?format=csv|xlsx|pdf`; GET `/org/import-template?format=`; POST `/org/nodes/{id}/import/preview` and `/import`



\## Database (migrations in order, Alembic, hand-written, `alembic check` clean)

1 settings schema + app\_setting; 2 audit schema + partitioned audit\_log + append-only trigger; 3 iam.user\_account; 4 iam.user\_session; 5 user\_account.full\_name; 6 org.node\_type, node\_type\_parent, node; 7 node.code nullable + settings.asset.



\## Project structure and files

```

varcity/

&#x20; .gitignore  README.md

&#x20; docs/        (PROGRESS.md = this file; otherwise empty)

&#x20; deploy/      (empty)

&#x20; backend/

&#x20;   alembic.ini  pytest.ini  requirements.txt  .env  .env.example

&#x20;   migrations/  env.py  script.py.mako  versions/ (7 migrations above)

&#x20;   app/

&#x20;     main.py                  (lifespan prints setup code; includes all routers)

&#x20;     core/    config.py  db.py  base.py  ids.py  net.py  tabular.py

&#x20;     modules/

&#x20;       audit/     models.py  service.py

&#x20;       settings/  models.py  schemas.py  service.py  router.py  branding.py

&#x20;       iam/       models.py  passwords.py  tokens.py  schemas.py  service.py  deps.py  router.py

&#x20;       setup/     code.py  schemas.py  service.py  router.py

&#x20;       org/       models.py  schemas.py  service.py  bulk.py  router.py

&#x20;   scripts/  create\_dev\_user.py   (dev helper; wizard replaces it)

&#x20;   tests/    conftest.py (fixtures: db, make\_user, signed\_in), test\_health, test\_audit,

&#x20;             test\_branding, test\_passwords, test\_user\_account, test\_auth, test\_setup,

&#x20;             test\_admin\_unlock, test\_org, test\_org\_bulk, test\_university\_settings

&#x20; frontend/

&#x20;   index.html  package.json  vite.config.js (React + Tailwind v4 plugin + /api proxy)

&#x20;   src/

&#x20;     main.jsx  index.css (theme variables)  App.jsx (Gate: setup -> login -> shell + routes)

&#x20;     navigation.js

&#x20;     lib/        api.js  color.js  format.js

&#x20;     auth/       auth-context.js  AuthProvider.jsx

&#x20;     theme/      branding-context.js  BrandingProvider.jsx

&#x20;     pages/      LoginPage.jsx  SetupPage.jsx

&#x20;     components/ BrandLogo.jsx  BrandBackdrop.jsx  VarcityLogo.jsx  ColourPreview.jsx

&#x20;       layout/   AppShell.jsx

&#x20;       ui/       styles.js  PageHeader.jsx  SectionCard.jsx  Field.jsx  Toggle.jsx  FormActions.jsx

&#x20;     features/

&#x20;       org/      org-api.js  tree.js  OrganizationPage.jsx  NodePage.jsx  ChildrenSection.jsx

&#x20;                 DetailsSection.jsx  ManageSection.jsx  ImportExportSection.jsx  InitializePanel.jsx

&#x20;       settings/ GeneralSettingsPage.jsx  UniversityTab.jsx  AppearanceTab.jsx  RegionalTab.jsx

&#x20;                 useProfileSection.js

```

Removed along the way (do not recreate): Modal.jsx, NodeTree.jsx, NodeDialogs.jsx, SettingsLayout.jsx, UniversityPage.jsx.



\## Known loose ends (not blockers)

\- Duplicated colour-preview markup in SetupPage vs `ColourPreview.jsx`; RegionalTab does not use `FormActions` yet; older files have more comments than my current preference.

\- No frontend tests yet (plan: Vitest + Testing Library). Backend tests are thorough.

\- Not built yet: password reset and email service, 2FA, roles/permissions, workflow engine, background jobs (needed for audit partitions, session cleanup, email), SSO/IdP, number-format engine, directory, caching, monitoring, HA/DR, offline/PWA, architecture docs and ADRs (the brief requires them; `docs/` is nearly empty).

\- Client IP behind Nginx needs a trusted-proxy setting (deployment phase). Session timeouts are env config for now and should become settings with the Security tab. Logo SVG not supported (sanitisation needed).



\## Agreed roadmap after Step 21

22 programme \*\*levels per department\*\*, \*\*programmes (courses)\*\* with codes (like EB3), dated department assignment history (courses can move departments), \*\*offerings per campus\*\*, deletion rules (cannot delete a course with students/curricula; a department must move its courses first) | then registration-number \*\*format engine\*\* (templates such as `{PROG}-{SEQ:4}/{YYYY}`, `{PROG}-{CAMPUS}-{SEQ:4}/{YYYY}`, dynamic counter scopes) | directory: persons, identifiers (PF/employee no., registration no. per enrolment, national ID or birth certificate), staff/student import | users created from directory records | roles, permissions, scopes, 2FA, password reset/email | workflow engine | academic calendar | grading schemes, assessment patterns, classification and progression rules | unit catalogue and curricula | cohorts and enrolments (incl. mature entry) | admissions processing (approved applicants, auto reg numbers, admission letters from templates, email) | unit registration, marks, results, transcripts | fees | reliability/performance/HA/offline | SSO/IdP | Docker packaging last.



\## Step 22: what I want you to do first

Do not design or code yet. \*\*Ask me questions first\*\*, grouped and short, covering at least:

\- Which fields a course/programme has (full name, short name, code format, award title, level, duration and its unit, mode of study such as full-time/part-time/distance/evening, credit total, regulator or accreditation reference, status/lifecycle such as proposed/approved/active/phased-out).

\- Programme levels: the default list per university, and how a department declares which levels it offers.

\- Whether a course belongs to exactly one department at a time, how history of moves should look, and who may approve moves.

\- Offerings per campus: what is recorded (intake months, mode, capacity, campus-specific code or fee), and how this ties to cohorts later.

\- Import/export columns I want for courses.

\- Anything else you think is needed before designing it.

After my answers, give me a short design for approval (tables, rules, screens), then proceed backend first, then frontend, one confirmed step at a time.

