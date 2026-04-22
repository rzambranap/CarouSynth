# CarouSynth

Web app for generating a randomized 10-slide Instagram carousel, then refining the composition manually in the browser before export.

## What it does

1. **Upload** — drag & drop (or click to browse) at least 10 images.
2. **Configure** — choose a seed for reproducibility and how many images to spread across the 10 slides.
3. **Generate** — the Flask backend builds a randomized long-canvas composition.
4. **Adjust** — drag, resize, and reorder images on the canvas; change the background colour and zoom level.
5. **Export** — download a ZIP containing a named folder with `carousel_01.png` … `carousel_10.png` and `layout.json`.

## Quick start (local)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Deploy to Render / Railway / Heroku

The repo ships with a `Procfile` so any Heroku-compatible platform can deploy it in one click:

1. Push the repo to GitHub.
2. Create a new web service on [Render](https://render.com), [Railway](https://railway.app), or Heroku and connect the repo.
3. The platform picks up the `Procfile` automatically and runs `gunicorn`.

No environment variables are required for basic use.

## Deploy with Docker

```bash
docker build -t carousynth .
docker run -p 8080:8080 carousynth
```

Then open `http://localhost:8080`.

## Notes

- Upload at least 10 unique images (duplicates are filtered by content hash).
- The requested image count is capped by the number of unique uploads.
- The UI uses downsampled previews for responsiveness; export rebuilds slides at full resolution from the layout data.
- Use **Advanced / Layout JSON** in the sidebar to save or restore a layout.

## Repo structure

- `app.py` — Flask backend and randomized layout generator.
- `templates/index.html` — browser UI.
- `requirements.txt` — Python dependencies (`Flask`, `Pillow`, `gunicorn`).
- `Procfile` — one-line process declaration for cloud platforms.
- `Dockerfile` — containerised deployment.
- `run.sh` — quick local launcher.
