import os, re, subprocess
OUT = "/tmp/input_video.mp4"
def get_video(source, url):
    print(f"Downloading from {source}: {url}")
    if source == "youtube":
        cmd = ["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", 
               "--merge-output-format", "mp4", "--force-ipv4", "-o", OUT, url]
        subprocess.run(cmd, check=True)
    elif source == "drive":
        import gdown
        m = re.search(r"/d/([a-zA-Z0-9_-]+)", url) or re.search(r"id=([a-zA-Z0-9_-]+)", url)
        if not m: raise ValueError("URL Drive tidak valid")
        gdown.download(id=m.group(1), output=OUT, quiet=False)
    return OUT
