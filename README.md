# Auto Watermark Remover (GitHub Actions)

Pemrosesan video penghapus watermark otomatis, dijalankan penuh oleh GitHub Actions.

## Cara Pakai
1. Buka tab **Actions** di repo ini.
2. Pilih workflow **"Remove Watermark"** di sidebar kiri.
3. Klik **"Run workflow"** → isi form:
   - **video_source**: `youtube` | `drive` | `upload_url`
   - **video_url**: link YouTube atau Google Drive (share link)
   - **method**: `repaint` (inpainting) | `crop` (potong area watermark)
4. Klik **Run workflow**.
5. Setelah selesai, hasil video otomatis ter-upload sebagai **Release** di tab **Releases**.

## Metode
- **repaint**: area watermark di-inpainting (background diisi ulang, watermark hilang, resolusi tetap).
- **crop**: video dipotong agar watermark hilang (resolusi berubah, lebih cepat).
