# Project 02: Docker Layer Caching & CI Pipeline di GitHub Actions

> **Catatan:** File `README.md` ini berisi panduan awal pengerjaan project. Setelah `Dockerfile` dan workflow CI kamu berhasil berjalan serta eksperimen *cache hit* / *cache invalidation* terbukti di GitHub Actions, silakan tulis ulang file ini untuk mendokumentasikan arsitektur, konfigurasi, dan hasil pengujian sebagai portofolio GitHub kamu.

---

## 1. Prasyarat (Prerequisites)

1. **Lingkungan Lokal (Ubuntu VM di VirtualBox):**
   - Docker Engine terinstal dan berjalan (`docker --version`).
   - Git terkonfigurasi dan terhubung ke repositori monorepo GitHub kamu (`docker-portfolio`).
2. **Repositori GitHub:**
   - Memiliki repositori GitHub (misalnya `docker-portfolio`) dengan GitHub Actions aktif.
3. **Pemahaman Konsep:**
   - Struktur `Dockerfile` (`FROM`, `WORKDIR`, `COPY`, `RUN`, `EXPOSE`, `CMD`).
   - Urutan *layer* dan mekanisme *cache invalidation* pada Docker build.

---

## 2. Struktur Folder Target (Monorepo)

Karena kamu menggunakan satu repositori berisi kumpulan project, folder `.github/workflows/` berada di **root repositori**, sedangkan kode aplikasi berada di dalam subfolder `project-02/`:

```text
docker-portfolio/                  # Root repositori GitHub
├── .github/
│   └── workflows/
│       └── ci-docker.yml          # [KAMU BUAT] Workflow GitHub Actions untuk Docker CI + Cache
├── project-1/
└── project-02/
    ├── app.py                     # Kode utama Python (Release Gatekeeper API)
    ├── requirements.txt           # Daftar dependensi (Flask, Gunicorn, Pydantic)
    ├── .dockerignore              # File/folder yang dikecualikan dari build context
    ├── Dockerfile                 # [KAMU BUAT] Konfigurasi image yang ramah layer caching
    └── README.md                  # Panduan & dokumentasi project
```

---

## 3. Instruksi Pengerjaan

### Langkah 1: Ekstrak Project ke dalam Monorepo
Pindahkan `project-02.zip` ke direktori root repositori kamu di Ubuntu VM, lalu ekstrak:
```bash
cd ~/docker-portfolio
unzip project-02.zip
cd project-02
```

### Langkah 2: Buat `Dockerfile` dengan Optimasi Layer Cache
Buat file `Dockerfile` di dalam `project-02/` dengan memperhatikan urutan instruksi agar *dependency layer* terpisah dari *application code layer*:

1. **`FROM`**: Gunakan *base image* `python:3.11-slim`.
2. **`WORKDIR`**: Set direktori kerja ke `/app`.
3. **`COPY` (Tahap 1 — Dependencies):** Salin `requirements.txt` saja terlebih dahulu ke `/app`.
4. **`RUN`**: Instal seluruh dependensi dengan `pip install --no-cache-dir -r requirements.txt`.
5. **`COPY` (Tahap 2 — Source Code):** Salin sisa file aplikasi (`app.py`) ke `/app`.
6. **`EXPOSE`**: Deklarasikan port `5000`.
7. **`CMD`**: Jalankan aplikasi menggunakan `python app.py` (format *exec* JSON array).

*(Uji terlebih dahulu secara lokal di Ubuntu VM menggunakan `docker build` dan `docker run` untuk memastikan container berjalan normal sebelum masuk ke tahap CI).*

### Langkah 3: Buat Workflow GitHub Actions (`ci-docker.yml`)
Buat file `.github/workflows/ci-docker.yml` di **root repositori** (`~/docker-portfolio/.github/workflows/ci-docker.yml`) dengan ketentuan berikut:

1. **Trigger (`on`):**
   - Jalankan pada event `push` dan `pull_request` ke branch `main`.
   - Gunakan filter `paths` agar workflow hanya berjalan saat ada perubahan pada `project-02/**` atau `.github/workflows/ci-docker.yml`.
2. **Setup Docker Buildx:**
   - Gunakan action `docker/setup-buildx-action@v3` (wajib ada agar fitur *cache backend* GitHub Actions dapat digunakan).
3. **Build Image dengan GitHub Actions Cache:**
   - Gunakan action `docker/build-push-action@v6` dengan parameter penting berikut:
     - `context: ./project-02`
     - `file: ./project-02/Dockerfile`
     - `tags: release-gatekeeper:ci`
     - `push: false` (karena fokus kita pada build & cache validation di CI, tanpa registry eksternal)
     - `load: true` (memuat hasil *build image* ke Docker daemon lokal runner agar bisa diuji di langkah berikutnya)
     - `cache-from: type=gha`
     - `cache-to: type=gha,mode=max`
4. **Container Smoke Test di CI:**
   - Tambahkan langkah `run` setelah build untuk menjalankan container dari `release-gatekeeper:ci` di background (`-d -p 5000:5000`), menunggu 2–3 detik, lalu menguji endpoint `http://localhost:5000/health` menggunakan `curl -f` agar pipeline gagal otomatis jika aplikasi crash saat dijalankan.

### Langkah 4: Uji Cache Hit & Cache Invalidation di GitHub Actions
Lakukan 3 kali *push* bertahap untuk membuktikan cara kerja cache di log GitHub Actions:

1. **Push Pertama (Cold Build / Cache Miss):**
   - Commit dan push `project-02/` beserta `.github/workflows/ci-docker.yml`.
   - Amati log step build di tab **Actions**: seluruh layer dijalankan dari awal (`RUN pip install` memakan waktu beberapa detik) dan di akhir step terdapat proses *exporting cache*.
2. **Push Kedua (Code Change / Cache Hit pada Dependencies):**
   - Ubah sedikit kode di `project-02/app.py` (misalnya tambahkan komentar atau ubah nilai default `APP_VERSION` menjadi `"1.0.1"`), lalu commit & push.
   - Amati log build di GitHub Actions: instruksi `COPY requirements.txt .` dan `RUN pip install ...` harus berstatus **`CACHED`**, dan hanya `COPY . .` yang dieksekusi ulang!
3. **Push Ketiga (Dependency Change / Cache Invalidation):**
   - Tambahkan satu library ringan di `project-02/requirements.txt` (misalnya `python-dotenv==1.0.1`), lalu commit & push.
   - Amati log build: karena checksum `requirements.txt` berubah, layer `COPY requirements.txt .` mengalami *cache miss* dan memaksa `RUN pip install ...` dijalankan ulang.

---

## 4. Goals Project-02 (Kriteria Keberhasilan)

Project-02 dinyatakan **berhasil** apabila seluruh kriteria berikut terpenuhi:

- [ ] **Dockerfile Optimal:** `Dockerfile` memisahkan layer instalasi `requirements.txt` dan penyalinan kode aplikasi dengan benar.
- [ ] **CI Pipeline Hijau (Passing):** Workflow `.github/workflows/ci-docker.yml` berjalan otomatis saat push ke `project-02/` dan lulus tahap *build* maupun *smoke test* `curl`.
- [ ] **Cache Hit Terbukti di CI:** Pada perubahan file `app.py`, log GitHub Actions menampilkan status `CACHED` pada layer `RUN pip install`.
- [ ] **Cache Invalidation Terbukti di CI:** Pada perubahan file `requirements.txt`, log GitHub Actions menginvalidasi cache dan membangun ulang layer dependensi.
- [ ] **Dokumentasi Portofolio Selesai:** File `README.md` telah diperbarui dengan penjelasan project, potongan log/bukti perbedaan waktu *cache miss* vs *cache hit*, serta penjelasan konfigurasi CI-nya.
