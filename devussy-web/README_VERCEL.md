# Deploying devussy-web to Vercel

This document covers how to deploy `devussy-web` to Vercel, and how to provide an API key for LLM usage. It also shows the insecure 'baked-in' option at your request and the recommended secure approach.

Important: Do NOT commit real secrets into code or repo history if you can avoid it. Use Vercel's project environment variables or the `vercel` CLI to set secrets securely.

Prerequisites
- Install Vercel CLI: `npm i -g vercel`
- Create/login to a Vercel account: `vercel login`

Recommended secure approach (preferred)
1. From your local project root, log in and link your project: `vercel --prod` and follow the prompts to link the directory.
2. Add the Requesty API key to Vercel's environment securely using the CLI or dashboard:
   - CLI: `vercel env add REQUESTY_API_KEY production` (you will be prompted to enter the secret value)
   - Dashboard: Project → Settings → Environment Variables → Add `REQUESTY_API_KEY`
3. Deploy: `vercel --prod`
4. The front-end and Python serverless functions under `api/` will be available at `/api/*`.

Baked-in (insecure) option — place the secret into the Vercel config
1. If you truly want to bake the API key into the repo (not recommended), the placeholder is added to `vercel.json` under `env.REQUESTY_API_KEY` — replace `REPLACE_WITH_YOUR_REQUESTY_API_KEY` with your key.
   - Warning: this adds your secret to repo files and may leak it to anyone with commit access. It's best avoided in public repos.
2. Commit and push; deploy using `vercel --prod`.

Notes about streaming and SSE endpoints
- Vercel serverless functions generally don't support full SSE / long-lived streaming connections the same way a dedicated backend (like your local Python dev server) does. The design endpoint here is implemented as a synchronous JSON response in `api/vercel_design.py`.
- If you need SSE-style streaming of tokens to the frontend, consider deploying the Python backend to a separate server (e.g., DigitalOcean, Railway, Render) and configure the Next frontend to call that backend via a Vercel rewrite. Alternatively convert streaming endpoints to Node/Edge functions in Next.js.

Mapping explanation
- We created a Vercel wrapper `api/vercel_design.py` to use the same generation logic while keeping the local `api/design.py` (dev-server-specific HTTP handler) intact.
- `vercel.json` includes a routing rule mapping `/api/design` to `/api/vercel_design` during Vercel deployment, so your frontend requests keep the same path.


Debugging & local development
- Run local dev server: `npm run dev` (Next dev server). If you want the Next frontend to talk to the local Python backend, set `USE_LOCAL_API=true` in your `.env` before running dev.
  - Example: `set USE_LOCAL_API=true; npm run dev` (PowerShell Windows)

Notes & Vercel specifics
- `next.config.ts` has logic to use the local proxy only in development or when `USE_LOCAL_API=true`.
- The Python serverless wrappers are in `api/vercel_design.py` (they read `REQUESTY_API_KEY` from environment if not set elsewhere).

If you want me to (optionally):
- Add wrappers for other `api/` endpoints to make them Vercel-compatible (e.g., `index`, `hand-off`, etc.).
- Add `vercel` GitHub Action automation for deploys on push to `main`/`production` branch.

Questions? Tell me which approach you prefer and I can adjust the repo (add wrappers for more endpoints or fully convert the Python API server to an async Vercel-compatible structure).
