# Enterprise Knowledge Copilot Frontend

React 18 + TypeScript + Vite + Tailwind UI for querying the Enterprise Knowledge Copilot backend.

## Local Development

```bash
npm install
npm run dev
```

Copy `.env.example` to `.env` if you need to change the API base URL.

```bash
VITE_API_URL=http://localhost:8000
```

## Docker

The root `docker-compose.yml` builds this frontend and serves it on port `3000` through Nginx.

```bash
docker compose up --build frontend
```

## Netlify

The root `netlify.toml` builds this app with `npm run build` from the `frontend/` directory. Set `VITE_API_URL` in Netlify to the deployed Railway backend URL before building:

```bash
VITE_API_URL=https://<your-railway-backend-domain>
```
