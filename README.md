# CarouSynth

Browser app for generating a randomized 10-slide Instagram carousel, then refining the composition manually before export.

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

## Deploy to Render (free tier)

1. Push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New → Web Service**.
3. Connect your GitHub repo.
4. Render auto-detects the `Procfile`. Accept the defaults and click **Deploy**.
5. The app will be live at the URL Render provides.

## Deploy to Heroku

```bash
heroku create
git push heroku main
heroku open
```

## Deploy to Railway

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**.
2. Select this repo. Railway reads the `Procfile` automatically.
3. Click **Deploy**.

## Notes

- Upload at least 10 unique images.
- Duplicate uploads are filtered by file content hash.
- The requested image count is capped by the number of unique uploads (max 200).
- The UI uses downsampled previews for responsiveness; export uses the full-resolution layout data.
- Upload limit is 200 MB per request.

## Repo structure

- `app.py` — Flask backend and randomized layout generator.
- `templates/index.html` — browser UI.
- `requirements.txt` — Python dependencies (`Flask`, `Pillow`, `gunicorn`).
- `Procfile` — tells PaaS hosts to serve with Gunicorn.
- `run.sh` — quick local launcher.
