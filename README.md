# CarouSynth

Local app for generating a randomized 10-slide Instagram carousel, then refining the composition manually in the browser before export.

## What it does

- Upload images in the UI.
- Set a seed and the number of images to use.
- Click **Generate layout**.
- The Flask backend builds a randomized long-canvas composition.
- The browser UI lets you drag, resize, reorder, import/export JSON, and export a ZIP.
- Export creates a ZIP containing a named folder with `carousel_01.png` to `carousel_10.png` and `layout.json`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Notes

- Upload at least 10 unique images.
- Duplicate uploads are filtered by file content hash.
- The requested image count is capped by the number of unique uploads.
- The UI uses downsampled previews for responsiveness, but export uses the layout data to build the final slides.

## Repo structure

- `app.py` — Flask backend and randomized layout generator.
- `templates/index.html` — browser UI.
- `requirements.txt` — Python dependencies.
- `run.sh` — quick launcher.
- `.gitignore` — Python local env ignores.
