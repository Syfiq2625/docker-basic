# Project 05: Multi-Stage Dockerfile, Non-Root Security & Buildx Cache Scope di CI

> **Catatan:** File `README.md` ini berisi panduan awal pengerjaan project. Setelah kamu berhasil membangun *multi-stage* `Dockerfile` dan workflow CI (`ci-project-05.yml`) serta memverifikasi seluruh aspek keamanan dan *cache scope* di GitHub Actions, silakan tulis ulang file ini untuk mendokumentasikan arsitektur, perbandingan ukuran image, dan hasil pengujian sebagai portofolio GitHub kamu.

---

## 1. Peningkatan Level dari Project Sebelumnya

Pada project ini kita masih berfokus pada **satu aplikasi tunggal** dan menggunakan **`docker buildx build` CLI** secara langsung (tanpa `build-push-action`), namun naik satu tingkat dengan menerapkan standar *production-grade* pada `Dockerfile` dan CI:

1. **Multi-Stage Build (`AS builder` & `COPY --from=builder`):** Memisahkan tahap kompilasi/instalasi dependensi (`virtual environment` di `/opt/venv`) dari *runtime image* akhir agar ukuran image lebih ramping dan bebas *build tools* yang tidak perlu.
2. **Container Hardening (Non-Root `USER`):** Membuat user khusus (`appuser`) sehingga proses Python tidak berjalan sebagai `root` (`UID 0`). Endpoint `/health` secara otomatis akan mengembalikan HTTP `503` jika container masih berjalan sebagai `root`!
3. **Build-Time & Runtime Variables (`ARG` & `ENV`):** Menyuntikkan metadata versi aplikasi (`APP_VERSION`) saat proses `docker buildx build --build-arg` dan mengatur variabel runtime Python (`PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`).
4. **Native Docker `HEALTHCHECK`:** Menanamkan instruksi pengecekan kesehatan container langsung di dalam `Dockerfile` sehingga status kesehatan terpantau oleh Docker daemon (`healthy` / `unhealthy`).
5. **Scoped Buildx Cache (`scope=project-05`):** Mengisolasi cache GitHub Actions khusus untuk `project-05` agar tidak bertabrakan dengan cache project lain di dalam satu monorepo.

---

## 2. Prasyarat (Prerequisites)

1. **Lingkungan Lokal (Ubuntu VM di VirtualBox):**
   - Docker Engine dengan dukungan Docker Buildx (`docker buildx version`).
   - Git terhubung ke repositori monorepo GitHub kamu (`docker-portfolio`).
2. **Repositori GitHub:**
   - GitHub Actions aktif pada repositori monorepo kamu.

---

## 3. Struktur Folder Target (Monorepo)

```text
docker-portfolio/                      # Root repositori GitHub
├── .github/
│   └── workflows/
│       └── ci-project-05.yml          # [KAMU BUAT] Workflow CI dengan Buildx & cache scope
├── project-1/
├── project-02/
└── project-05/
    ├── app.py                         # Kode utama Python (Container Security & Config Audit API)
    ├── requirements.txt               # Daftar dependensi (Flask, Gunicorn, Pydantic)
    ├── .dockerignore                  # File/folder yang dikecualikan dari build context
    ├── Dockerfile                     # [KAMU BUAT] Multi-stage Dockerfile + Non-root + HEALTHCHECK
    └── README.md                      # Panduan & dokumentasi project
```

---

## 4. Instruksi Pengerjaan

### Langkah 1: Ekstrak Project ke dalam Monorepo
Pindahkan `project-05.zip` ke root repositori kamu di Ubuntu VM, lalu ekstrak:
```bash
cd ~/docker-portfolio
unzip project-05.zip
cd project-05
```

### Langkah 2: Buat Multi-Stage `Dockerfile`
Buat file `Dockerfile` di dalam `project-05/` dengan struktur **2 stage** berikut:

#### Stage 1: `builder`
1. **`FROM python:3.11-slim AS builder`**: Gunakan image dasar sebagai stage pembangun.
2. **`WORKDIR /build`**: Tentukan direktori kerja sementara untuk tahap build.
3. **`RUN python -m venv /opt/venv`**: Buat *isolated virtual environment* di `/opt/venv`.
4. **`ENV PATH="/opt/venv/bin:$PATH"`**: Arahkan `PATH` agar perintah `pip` otomatis menginstal paket ke dalam `/opt/venv`.
5. **`COPY requirements.txt .`** dan **`RUN pip install --no-cache-dir -r requirements.txt`**: Instal seluruh dependensi ke dalam virtual environment.

#### Stage 2: `runtime` (Final Image)
1. **`FROM python:3.11-slim`**: Mulai stage kedua yang bersih tanpa sisa cache build.
2. **`ARG APP_VERSION=1.0.0`**: Definisikan argumen build untuk versi aplikasi.
3. **`ENV`**: Set variabel lingkungan berikut:
   - `PYTHONDONTWRITEBYTECODE=1`
   - `PYTHONUNBUFFERED=1`
   - `PATH="/opt/venv/bin:$PATH"`
   - `APP_VERSION=${APP_VERSION}`
   - `PORT=8080`
4. **`RUN` (Non-Root User):** Buat grup dan user sistem tanpa hak root (misalnya `groupadd -r appgroup && useradd -r -g appgroup appuser`).
5. **`WORKDIR /app`**: Tentukan direktori kerja aplikasi.
6. **`COPY --from=builder /opt/venv /opt/venv`**: Salin hanya hasil virtual environment dari Stage 1 (`builder`) ke Stage 2.
7. **`COPY --chown=appuser:appgroup app.py .`**: Salin kode aplikasi dengan kepemilikan langsung milik `appuser`.
8. **`USER appuser`**: Beralih dari `root` ke `appuser` sebelum menjalankan aplikasi.
9. **`EXPOSE 8080`**: Dokumentasikan port aplikasi (`8080` — *non-privileged port* untuk non-root user).
10. **`HEALTHCHECK`**: Tambahkan instruksi pengecekan kesehatan bawaan Docker (gunakan Python `urllib.request` agar tidak perlu menginstal `curl` tambahan di dalam image):
    ```dockerfile
    HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
      CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1
    ```
11. **`CMD ["python", "app.py"]`**: Jalankan aplikasi menggunakan format *exec*.

### Langkah 3: Uji Lokal di Ubuntu VM
Sebelum membuat file CI, uji dulu `Dockerfile` kamu secara lokal:
```bash
docker buildx build --build-arg APP_VERSION=1.0.0 --load -t security-audit:1.0 .
docker run -d -p 8080:8080 --name audit-test security-audit:1.0
```
Tunggu sekitar 10–15 detik, lalu verifikasi:
1. **Status Health Native Docker:**
   ```bash
   docker inspect --format='{{.State.Health.Status}}' audit-test
   ```
   *(Output wajib: `healthy`)*
2. **Verifikasi User Non-Root:**
   ```bash
   docker exec audit-test whoami
   curl -s http://localhost:8080/security
   ```
   *(Pastikan user adalah `appuser`, `"is_non_root": true`, dan `"virtual_env": "/opt/venv"`).*
3. **Hapus container uji lokal:**
   ```bash
   docker stop audit-test && docker rm audit-test
   ```

### Langkah 4: Buat Workflow CI (`ci-project-05.yml`)
Buat file `.github/workflows/ci-project-05.yml` di **root repositori** (`~/docker-portfolio/.github/workflows/ci-project-05.yml`) dengan ketentuan berikut:

1. **Trigger & Working Directory:**
   - Trigger pada `push` dan `pull_request` ke branch `main` dengan filter `paths` untuk `project-05/**` dan `.github/workflows/ci-project-05.yml`, serta `workflow_dispatch`.
   - Set `defaults.run.working-directory: './project-05'`.
2. **Setup Buildx:**
   - Gunakan `docker/setup-buildx-action@v3` dengan `driver: docker-container`.
3. **Build dengan Buildx, `--build-arg`, dan Scoped Cache:**
   - Jalankan `docker buildx build` dengan opsi:
     - `--load`
     - `--build-arg APP_VERSION=${{ github.sha }}`
     - `--cache-from type=gha,scope=project-05`
     - `--cache-to type=gha,mode=max,scope=project-05`
     - `--tag security-audit:${{ github.sha }}`
     - `.`
4. **Automated Security & Health Verification di CI:**
   - Jalankan container di background (`-d -p 8080:8080 --name audit-ci security-audit:${{ github.sha }}`).
   - Pastikan container berjalan bukan sebagai root (`test "$(docker exec audit-ci whoami)" = "appuser"`).
   - Tunggu beberapa detik hingga status health container menjadi `healthy`, lalu uji endpoint `curl -f http://localhost:8080/health` dan `curl -f http://localhost:8080/security`.
   - Tambahkan step pembersihan dengan `if: always()` untuk `docker stop` dan `docker rm`.

---

## 5. Goals Project-05 (Kriteria Keberhasilan)

Project-05 dinyatakan **berhasil** apabila seluruh poin berikut terpenuhi:

- [ ] **Multi-Stage Build Berhasil:** Image berhasil dibangun dari 2 stage (`builder` dan `runtime`) tanpa menyertakan cache/sisa build di image akhir.
- [ ] **Non-Root Container Terverifikasi:** Perintah `whoami` di dalam container menghasilkan `appuser` (bukan `root`), dan endpoint `/health` mengembalikan HTTP `200 OK` (`"status": "healthy"`).
- [ ] **Native `HEALTHCHECK` Berfungsi:** `docker inspect` menampilkan status kesehatan container `healthy`.
- [ ] **Build-Time `ARG` Terinjeksi:** Endpoint `/security` menampilkan nilai `version` sesuai dengan `--build-arg APP_VERSION` yang dikirim saat build.
- [ ] **Scoped Buildx Cache Berjalan di CI:** Pada push kedua yang hanya mengubah `app.py`, stage `builder` (`RUN pip install`) berstatus `CACHED` di log GitHub Actions menggunakan `scope=project-05`.
- [ ] **Dokumentasi Portofolio Lengkap:** File `README.md` telah kamu perbarui untuk menjelaskan konsep *multi-stage build*, keamanan *non-root user*, `HEALTHCHECK`, serta konfigurasi CI-nya.
