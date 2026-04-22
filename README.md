# CarouSynth

Web app for generating a randomized 10-slide Instagram carousel, then refining the composition manually in the browser before export.

## What it does

- Upload images in the UI.
- Set a seed and the number of images to use.
- Click **Generate layout**.
- The Flask backend builds a randomized long-canvas composition.
- The browser UI lets you drag, resize, reorder, import/export JSON, and export a ZIP.
- Export creates a ZIP containing a named folder with `carousel_01.png` to `carousel_10.png` and `layout.json`.

## Quick start (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

To enable debug mode locally:

```bash
FLASK_DEBUG=1 python app.py
```

## Deploy to Render (free tier)

1. Fork or push this repo to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com) and connect your repo.
3. Render will auto-detect `render.yaml` and configure the service.
4. Set the `SECRET_KEY` environment variable in the Render dashboard (or let `render.yaml` auto-generate one).
5. Click **Deploy** — the app will be live at your Render URL.

The `Procfile` is also compatible with **Heroku**, **Railway**, and **Fly.io**.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | random bytes | Flask session secret — set a stable value in production |
| `PORT` | `5000` | Port the server binds to (set automatically by hosting platforms) |
| `FLASK_DEBUG` | `0` | Set to `1` to enable debug mode locally |

## Rate limits

To protect the free-tier hosting, the `/generate-layout` and `/export-layout` endpoints are limited to **10 requests per minute** per IP. Global limits are **200 requests per day** and **60 requests per hour** per IP.

## Notes

- Upload at least 10 unique images.
- Each uploaded image must be under 20 MB; total upload is capped at 200 MB.
- Duplicate uploads are filtered by file content hash.
- The requested image count is capped by the number of unique uploads.
- The UI uses downsampled previews for responsiveness, but export uses the layout data to build the final slides.

## Health check

`GET /health` returns `{"status": "ok"}` — used by hosting platforms to verify the service is running.

## Repo structure

- `app.py` — Flask backend and randomized layout generator.
- `templates/index.html` — browser UI.
- `requirements.txt` — Python dependencies.
- `Procfile` — Gunicorn start command for Heroku/Render/Railway.
- `render.yaml` — Render deployment configuration.
- `run.sh` — quick local launcher.
- `.gitignore` — Python local env ignores.
