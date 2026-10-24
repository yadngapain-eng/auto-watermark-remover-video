import os, cv2, numpy as np

INPUT = "/tmp/input_video.mp4"
OUTPUT = "/tmp/output_video.mp4"

def process_repaint(video_path):
    # Baca input custom text dari Environment Variable GitHub
    use_custom = os.environ.get("USE_CUSTOM", "false").lower() == "true"
    custom_text = os.environ.get("CUSTOM_TEXT", "").strip()
    
    cap = cv2.VideoCapture(video_path)
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Deteksi area watermark (Fokus di bagian atas)
    frames = []
    for i in np.linspace(0, max(total-2,0), 20).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
        ret, f = cap.read()
        if ret:
            top_part = f[0:int(H*0.3), :]
            frames.append(cv2.cvtColor(top_part, cv2.COLOR_BGR2GRAY))
            
    regions = []
    if frames:
        std = np.stack(frames, axis=0).astype(np.float32).std(axis=0)
        mask = (std < 15).astype(np.uint8) * 255
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((15,15),np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w > 50 and h > 20 and w < W*0.8:
                regions.append((x, y, w, h))
    
    if not regions:
        regions = [(int(W*0.2), int(H*0.05), int(W*0.6), int(H*0.1))]
        
    print(f"Area watermark terdeteksi: {regions}")
    
    out = cv2.VideoWriter(OUTPUT, cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))
    mask = np.zeros((H, W), dtype=np.uint8)
    
    for (x, y, w, h) in regions:
        pad = 10
        mask[max(0,y-pad):min(H,y+h+pad), max(0,x-pad):min(W,x+w+pad)] = 255

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Hapus watermark lama
        frame = cv2.inpaint(frame, mask, 3, cv2.INPAINT_TELEA)
        
        # Jika checkbox dicentang DAN teks tidak kosong, timpa dengan teks baru
        if use_custom and custom_text:
            for (x, y, w, h) in regions:
                text_size = cv2.getTextSize(custom_text, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 3)[0]
                tx = x + (w - text_size[0]) // 2
                ty = y + (h + text_size[1]) // 2
                
                # Outline hitam & Teks kuning
                cv2.putText(frame, custom_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,0,0), 5)
                cv2.putText(frame, custom_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0,255,255), 2)

        out.write(frame)
        
    cap.release(); out.release()

if __name__ == "__main__":
    process_repaint(INPUT)
