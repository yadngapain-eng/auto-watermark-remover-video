"""Downloader video dari YouTube atau Google Drive."""
import os, re, subprocess, sys

OUT = "/tmp/input_video.mp4"

def download_youtube(url: str) -> str:
    print(f"[DL] YouTube: {url}", flush=True)
    cmd = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--no-warnings", "--retries", "3",
        "-o", OUT, url,
    ]
    subprocess.run(cmd, check=True)
    if not os.path.exists(OUT):
        raise RuntimeError("Download YouTube gagal.")
    return OUT

def download_gdrive(url: str) -> str:
    print(f"[DL] Google Drive: {url}", flush=True)
    # Ekstrak ID dari berbagai format link Drive
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)",
        r"/d/([a-zA-Z0-9_-]+)",
    ]
    file_id = None
    for p in patterns:
        m = re.search(p, url)
        if m:
            file_id = m.group(1)
            break
    if not file_id:
        raise ValueError(f"Tidak bisa ekstrak file ID dari: {url}")

    # Pakai gdown (mendukung file besar > 100MB)
    import gdown
    gdown.download(id=file_id, output=OUT, quiet=False)
    if not os.path.exists(OUT):
        raise RuntimeError("Download Drive gagal. Pastikan file publik (Anyone with link).")
    return OUT

def download_direct(url: str) -> str:
    print(f"[DL] Direct URL: {url}", flush=True)
    import urllib.request
    urllib.request.urlretrieve(url, OUT)
    return OUT

def get_video(source: str, url: str) -> str:
    source = source.lower().strip()
    if source == "youtube":
        return download_youtube(url)
    elif source == "drive":
        return download_gdrive(url)
    elif source == "direct":
        return download_direct(url)
    else:
        raise ValueError(f"Sumber tidak dikenal: {source}")
