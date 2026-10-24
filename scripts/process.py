import os, cv2, numpy as np
from tqdm import tqdm
INPUT = "/tmp/input_video.mp4"
OUTPUT = "/tmp/output_video.mp4"

def detect_watermark(video_path):
    cap = cv2.VideoCapture(video_path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames = []
    idxs = np.linspace(0, max(total - 2, 0), 30).astype(int)
    for i in idxs:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
        ret, f = cap.read()
        if ret: frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    cap.release()
    
    if len(frames) < 3: 
        return [(int(W*0.7), int(H*0.85), int(W*0.28), int(H*0.13))]
    
    std = np.stack(frames, axis=0).astype(np.float32).std(axis=0)
    mask = (std < 8).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((7,7),np.uint8))
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    regions = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        # Filter: Abaikan UI YouTube (biasanya di pojok kiri bawah atau kanan)
        if (W*H*0.001) < (w*h) < (W*H*0.15) and w > 20 and h > 10:
            regions.append((x, y, w, h))
            
    return regions if regions else [(int(W*0.7), int(H*0.85), int(W*0.28), int(H*0.13))]

def main():
    method = os.environ.get("METHOD", "repaint")
    print(f"Metode: {method}")
    regions = detect_watermark(INPUT)
    print(f"Terdeteksi {len(regions)} area watermark: {regions}")
    
    cap = cv2.VideoCapture(INPUT)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    if method == "crop":
        xs = [r[0] for r in regions]
        ys = [r[1] for r in regions]
        cx1, cy1, cx2, cy2 = 0, 0, W, H
        if np.mean(xs) > W*0.5: cx2 = min(xs) - 5
        if np.mean(ys) > H*0.5: cy2 = min(ys) - 5
        if np.mean(xs) < W*0.5: cx1 = max([r[0]+r[2] for r in regions]) + 5
        if np.mean(ys) < H*0.5: cy1 = max([r[1]+r[3] for r in regions]) + 5
        out = cv2.VideoWriter(OUTPUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (cx2-cx1, cy2-cy1))
        print(f"Crop size: {cx2-cx1}x{cy2-cy1}")
    else:
        out = cv2.VideoWriter(OUTPUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
        mask = np.zeros((H, W), dtype=np.uint8)
        for (x, y, w, h) in regions:
            mask[max(0,y-4):min(H,y+h+4), max(0,x-4):min(W,x+w+4)] = 255

    pbar = tqdm(total=total)
    while True:
        ret, frame = cap.read()
        if not ret: break
        if method == "crop": out.write(frame[cy1:cy2, cx1:cx2])
        else: out.write(cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA))
        pbar.update(1)
    pbar.close(); cap.release(); out.release()

if __name__ == "__main__":
    main()
