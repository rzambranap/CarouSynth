from __future__ import annotations

import base64
import hashlib
import io
import json
import random
import re
import zipfile
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, jsonify, render_template, request, send_file
from PIL import Image, ImageOps

app = Flask(__name__)

POST_W = 1080
POST_H = 1350
N_POSTS = 10
BG_COLOR = "#ffffff"
MAX_TRIES = 120
PADDING_RATIO = 0.25
SPILL_LEFT = 0.6
SPILL_RIGHT = 1.6
DEFAULT_IMAGE_COUNT = 30
MAX_IMAGE_COUNT = 200


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def sanitize_folder_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (name or "carousel_export").strip())
    cleaned = cleaned.strip("._") or "carousel_export"
    return cleaned[:80]


def load_and_resize_from_bytes(blob: bytes, rng: random.Random) -> Image.Image:
    img = Image.open(io.BytesIO(blob)).convert("RGB")
    img = ImageOps.exif_transpose(img)
    w, h = img.size

    r = rng.random()
    if r < 0.20:
        target = rng.randint(240, 420)
    elif r < 0.75:
        target = rng.randint(450, 850)
    else:
        target = rng.randint(900, 1300)

    if w >= h:
        new_w = target
        new_h = int(h * target / w)
    else:
        new_h = target
        new_w = int(w * target / h)

    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def sample_local_position_with_spill(img_w: int, img_h: int, rng: random.Random) -> tuple[int, int]:
    clusters = [
        (0.50, 0.50, 0.20, 0.15, 0.30),
        (0.28, 0.24, 0.14, 0.10, 0.175),
        (0.72, 0.24, 0.14, 0.10, 0.175),
        (0.28, 0.76, 0.14, 0.10, 0.175),
        (0.72, 0.76, 0.14, 0.10, 0.175),
    ]
    weights = [c[4] for c in clusters]
    cx, cy, sx, sy, _ = rng.choices(clusters, weights=weights, k=1)[0]

    local_center_x = rng.gauss(cx * POST_W, sx * POST_W)
    local_center_y = rng.gauss(cy * POST_H, sy * POST_H)

    local_x = int(local_center_x - img_w / 2)
    local_y = int(local_center_y - img_h / 2)

    local_y = int(clamp(local_y, -img_h // 2, POST_H - img_h // 2))
    local_x = int(
        clamp(
            local_x,
            -int(SPILL_LEFT * POST_W) - img_w // 2,
            int(SPILL_RIGHT * POST_W) - img_w // 2,
        )
    )
    return local_x, local_y


def center_of_box(x: float, y: float, w: float, h: float) -> tuple[float, float]:
    return x + w / 2, y + h / 2


def make_zone(cx: float, cy: float, w: float, h: float, pad: float) -> tuple[float, float, float, float]:
    hw = (w * (1 + 2 * pad)) / 2
    hh = (h * (1 + 2 * pad)) / 2
    return (cx - hw, cy - hh, cx + hw, cy + hh)


def center_allowed(cx: float, cy: float, zones: List[tuple[float, float, float, float]]) -> bool:
    for x0, y0, x1, y1 in zones:
        if x0 <= cx <= x1 and y0 <= cy <= y1:
            return False
    return True


def image_to_data_url(img: Image.Image, fmt: str = "JPEG", quality: int = 88) -> str:
    buf = io.BytesIO()
    save_kwargs: Dict[str, Any] = {}
    if fmt.upper() == "JPEG":
        save_kwargs["quality"] = quality
    img.save(buf, format=fmt, **save_kwargs)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    mime = "image/jpeg" if fmt.upper() == "JPEG" else "image/png"
    return f"data:{mime};base64,{encoded}"


def split_nonempty(items: list[dict[str, Any]], n_sets: int, rng: random.Random) -> list[list[dict[str, Any]]]:
    if len(items) < n_sets:
        raise ValueError(f"Need at least {n_sets} images, got {len(items)}")
    shuffled = items[:]
    rng.shuffle(shuffled)
    sets = [[shuffled[i]] for i in range(n_sets)]
    for item in shuffled[n_sets:]:
        sets[rng.randrange(n_sets)].append(item)
    for subset in sets:
        rng.shuffle(subset)
    return sets


def read_unique_uploads(uploaded_files) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen = set()
    for idx, storage in enumerate(uploaded_files):
        raw = storage.read()
        if not raw:
            continue
        digest = hashlib.sha1(raw).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        unique.append({
            "raw": raw,
            "name": Path(storage.filename or f"image_{idx}").name,
        })
    return unique


def generate_layout(uploaded_files, seed: int, image_count: int) -> dict[str, Any]:
    rng = random.Random(seed)
    carousel_w = POST_W * N_POSTS
    carousel_h = POST_H

    unique_uploads = read_unique_uploads(uploaded_files)
    if len(unique_uploads) < N_POSTS:
        raise ValueError(f"Need at least {N_POSTS} unique images, got {len(unique_uploads)}")

    chosen_count = max(N_POSTS, min(image_count, len(unique_uploads), MAX_IMAGE_COUNT))
    selected_uploads = rng.sample(unique_uploads, chosen_count)

    images: list[dict[str, Any]] = []
    for idx, item in enumerate(selected_uploads):
        img = load_and_resize_from_bytes(item["raw"], rng)
        images.append(
            {
                "id": f"img_{idx}",
                "name": item["name"],
                "image": img,
                "src": image_to_data_url(img),
            }
        )

    sets = split_nonempty(images, N_POSTS, rng)
    zones: list[tuple[float, float, float, float]] = []
    items: list[dict[str, Any]] = []

    for frame_idx, frame_imgs in enumerate(sets):
        origin_x = frame_idx * POST_W
        for img_info in frame_imgs:
            img = img_info["image"]
            final_x = origin_x
            final_y = 0
            placed = False

            for _ in range(MAX_TRIES):
                lx, ly = sample_local_position_with_spill(img.width, img.height, rng)
                x = int(clamp(origin_x + lx, -img.width // 2, carousel_w - img.width // 2))
                y = int(clamp(ly, -img.height // 2, carousel_h - img.height // 2))
                cx, cy = center_of_box(x, y, img.width, img.height)
                if center_allowed(cx, cy, zones):
                    final_x, final_y = x, y
                    zones.append(make_zone(cx, cy, img.width, img.height, PADDING_RATIO))
                    placed = True
                    break

            if not placed:
                cx, cy = center_of_box(final_x, final_y, img.width, img.height)
                zones.append(make_zone(cx, cy, img.width, img.height, PADDING_RATIO))

            items.append(
                {
                    "id": img_info["id"],
                    "name": img_info["name"],
                    "src": img_info["src"],
                    "x": float(final_x),
                    "y": float(final_y),
                    "width": float(img.width),
                    "height": float(img.height),
                    "rotation": 0,
                }
            )

    rng.shuffle(items)

    return {
        "postWidth": POST_W,
        "postHeight": POST_H,
        "nPosts": N_POSTS,
        "background": BG_COLOR,
        "seed": seed,
        "imageCount": chosen_count,
        "items": items,
    }


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/generate-layout")
def generate_layout_route():
    files = request.files.getlist("images")
    try:
        seed = int(request.form.get("seed", random.randint(1, 10_000_000)))
    except ValueError:
        seed = random.randint(1, 10_000_000)

    try:
        image_count = int(request.form.get("image_count", DEFAULT_IMAGE_COUNT))
    except ValueError:
        image_count = DEFAULT_IMAGE_COUNT

    try:
        layout = generate_layout(files, seed, image_count)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    return jsonify(layout)


@app.post("/export-layout")
def export_layout_route():
    payload = request.get_json(force=True)
    folder_name = sanitize_folder_name(payload.get("folderName", "carousel_export"))
    layout = payload.get("layout") or {}
    items = layout.get("items") or []
    background = layout.get("background", BG_COLOR)
    if not items:
        return jsonify({"error": "Layout contains no items."}), 400

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for i in range(N_POSTS):
            left = i * POST_W
            slide = Image.new("RGB", (POST_W, POST_H), background)
            for item in items:
                src = item.get("src")
                if not src or not src.startswith("data:"):
                    continue
                try:
                    encoded = src.split(",", 1)[1]
                    raw = base64.b64decode(encoded)
                    img = Image.open(io.BytesIO(raw)).convert("RGB")
                    img = ImageOps.exif_transpose(img)
                except Exception:
                    continue
                x = int(round(float(item.get("x", 0)) - left))
                y = int(round(float(item.get("y", 0))))
                w = max(1, int(round(float(item.get("width", img.width)))))
                h = max(1, int(round(float(item.get("height", img.height)))))
                if img.size != (w, h):
                    img = img.resize((w, h), Image.Resampling.LANCZOS)
                slide.paste(img, (x, y))

            out = io.BytesIO()
            slide.save(out, format="PNG")
            zf.writestr(f"{folder_name}/carousel_{i + 1:02d}.png", out.getvalue())

        zf.writestr(f"{folder_name}/layout.json", json.dumps(layout, indent=2).encode("utf-8"))

    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/zip",
        as_attachment=True,
        download_name=f"{folder_name}.zip",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
