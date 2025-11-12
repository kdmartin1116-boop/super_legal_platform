# Sovereign Legal Demo

Lightweight demo app that shows how to call the backend prompt-rendering endpoint from a small React UI.

Usage
1. Install dependencies:

```bash
cd frontend/demo
npm install
npm run dev
```

2. Ensure the backend is running and reachable at the same host/port (or configure a proxy in Vite). The demo posts to `/api/v1/documents/prompts/render`.

Notes
- This is a minimal scaffold adapted from an external frontend. It demonstrates client-side usage of the server-side prompt-rendering API but is not production-ready.
