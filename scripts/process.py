\
"""Deteksi & hapus watermark otomatis dari video.

Metode:
  - repaint : inpainting area watermark (OpenCV cv2.inpaint)
  - crop    : potong sisi yang mengandung watermark

Deteksi: temporal std — area yang tidak berubah antar frame = watermark.
"""
import os, cv2, numpy as np
from tqdm import tqdm

INPUT = "/tmp/input_video.mp4"
OUTPUT = "/tmp/output_video.mp4"

def detect_watermark(video_path, sample_every=15, max_samples=40):
    print("[DET] Analisis frame...", flush=True)
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[DET] Video: {W}x{H}, {total} frame", flush=True)

    frames = []
    idxs = np.linspace(0, max(total - 2, 0), max_samples).astype(int)
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ret, f = cap.read()
        if not ret:
            break
        frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    cap.release()

    if len(frames) < 3:
        print("[DET] Frame kurang, fallback pojok kanan bawah.", flush=True)
        return [(int(W*0.7), int(H*0.85), int(W*0.28), int(H*0.13))]

    stack = np.stack(frames, axis=0).astype(np.float32)
    temporal_std = stack.std(axis=0)

    mask = (temporal_std < 8).astype(np.uint8) * 255
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    regions = []
    min_area = W * H * 0.0005
    max_area = W * H * 0.25
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if min_area < area < max_area and w > 20 and h > 10:
            if w > W * 0.9 or h > H * 0.9:
                continue
            regions.append((x, y, w, h))

    if not regions:
        print("[DET] Tidak ada kandidat, fallback pojok kanan bawah.", flush=True)
        regions = [(int(W*0.7), int(H*0.85), int(W*0.28), int(H*0.13))]

    print(f"[DET] {len(regions)} area: {regions}", flush=True)
    return regions

def process_repaint(video_path, regions):
    cap = cv2.VideoCapture(video_path)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    out = cv2.VideoWriter(OUTPUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    mask = np.zeros((H, W), dtype=np.uint8)
    for (x, y, w, h) in regions:
        pad = 4
        mask[max(0, y-pad):min(H, y+h+pad),
             max(0, x-pad):min(W, x+w+pad)] = 255

    pbar = tqdm(total=total, desc="Inpaint")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        out.write(frame)
        pbar.update(1)
    pbar.close(); cap.release(); out.release()

def process_crop(video_path, regions):
    cap = cv2.VideoCapture(video_path)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    xs = [r[0] for r in regions]
    ys = [r[1] for r in regions]
    x2s = [r[0] + r[2] for r in regions]
    y2s = [r[1] + r[3] for r in regions]

    cx1, cy1, cx2, cy2 = 0, 0, W, H
    if np.mean(xs) > W * 0.5: cx2 = min(xs) - 5
    if np.mean(ys) > H * 0.5: cy2 = min(ys) - 5
    if np.mean(xs) < W * 0.5: cx1 = max(x2s) + 5
    if np.mean(ys) < H * 0.5: cy1 = max(y2s) + 5
    cx1 = max(cx1, 0); cy1 = max(cy1, 0)
    cx2 = min(cx2, W); cy2 = min(cy2, H)

    ow, oh = cx2 - cx1, cy2 - cy1
    if ow < 100 or oh < 100:
        raise RuntimeError(f"Crop terlalu kecil ({ow}x{oh}), metode crop tidak cocok.")
    print(f"[CROP] Output {ow}x{oh}", flush=True)

    out = cv2.VideoWriter(OUTPUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (ow, oh))
    pbar = tqdm(total=total, desc="Crop")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame[cy1:cy2, cx1:cx2])
        pbar.update(1)
    pbar.close(); cap.release(); out.release()

def main():
    method = os.environ.get("METHOD", "repaint").lower()
    print(f"[PROC] Metode: {method}", flush=True)

    if not os.path.exists(INPUT):
        raise FileNotFoundError(f"Input tidak ada: {INPUT}")

    regions = detect_watermark(INPUT)

    if method == "repaint":
        process_repaint(INPUT, regions)
    elif method == "crop":
        process_crop(INPUT, regions)
    else:
        raise ValueError(f"Metode tidak dikenal: {method}")

    if not os.path.exists(OUTPUT):
        raise RuntimeError("Output tidak terbentuk.")
    size = os.path.getsize(OUTPUT) / 1e6
    print(f"[PROC] Selesai: {OUTPUT} ({size:.1f} MB)", flush=True)

if __name__ == "__main__":
    main()
