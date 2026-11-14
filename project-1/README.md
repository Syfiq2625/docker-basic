# Project 1: Containerizing Python Web API dengan Dockerfile

> **Catatan:** File `README.md` ini berisi panduan awal pengerjaan project. Setelah kamu berhasil mem-build image dan menjalankan container dengan sukses, silakan ubah isi file ini untuk mendokumentasikan penjelasan project, tujuan, materi `Dockerfile` yang digunakan, serta langkah konfigurasinya sebagai portofolio GitHub kamu.

---

## 1. Prasyarat (Prerequisites)

Pastikan lingkungan kerja di **Ubuntu Linux (VirtualBox)** kamu sudah memenuhi syarat berikut sebelum memulai:

1. **Docker Engine** sudah terinstal dan berjalan (`docker --version` dan `docker ps` berjalan tanpa `sudo`, atau gunakan `sudo`).
2. **Utility pendukung** di terminal Ubuntu: `unzip` dan `curl` (`sudo apt update && sudo apt install -y unzip curl`).
3. **Akses Editor:** Bisa menggunakan terminal langsung (`nano`/`vim`) atau **VS Code** di Windows yang terhubung ke Ubuntu VM melalui **Remote - SSH**.

---

## 2. Struktur Folder Awal

```text
project-1/
├── app.py              # Kode utama Python (Flask REST API sederhana)
├── requirements.txt    # Daftar dependensi library Python
├── .dockerignore       # Daftar file/folder yang diabaikan saat docker build
└── README.md           # Panduan instruksi project
```

*(Kamu akan menambahkan satu file baru bernama `Dockerfile` di dalam folder `project-1/` ini).*

---

## 3. Instruksi Pengerjaan

### Langkah 1: Pindahkan & Ekstrak Project ke Ubuntu VM
1. Pindahkan file `project-1-v2.zip` dari host Windows ke direktori kerja di Ubuntu VM (misalnya ke `~/docker-portfolio/` menggunakan `scp` atau Shared Folder VirtualBox).
2. Ekstrak file zip tersebut:
   ```bash
   cd ~/docker-portfolio
   unzip project-1-v2.zip
   cd project-1
   ```

### Langkah 2: Buat `Dockerfile`
Buat file bernama `Dockerfile` (tanpa ekstensi) di dalam folder `project-1/` dan susun instruksinya dengan memanfaatkan 6 materi berikut:

1. **`FROM`**: Gunakan *official base image* Python yang ringan, seperti `python:3.11-slim` atau `python:3.11-alpine`.
2. **`WORKDIR`**: Tentukan direktori kerja di dalam container, misalnya `/app`.
3. **`COPY`**:
   - Salin `requirements.txt` terlebih dahulu ke dalam `WORKDIR` (praktik *layer caching* yang baik).
   - Salin file aplikasi (`app.py` atau seluruh isi direktori `.`) ke dalam `WORKDIR`.
4. **`RUN`**: Jalankan perintah instalasi dependensi Python (`pip install --no-cache-dir -r requirements.txt`).
5. **`EXPOSE`**: Dokumentasikan bahwa container mendengarkan koneksi pada port `5000`.
6. **`CMD`**: Tentukan perintah utama yang dijalankan saat container menyala untuk menjalankan `app.py` menggunakan Python.

### Langkah 3: Build Docker Image
Jalankan perintah berikut dari dalam direktori `project-1/` (perhatikan tanda titik `.` di akhir perintah):
```bash
docker build -t node-inspector:1.0 .
```
Pastikan image berhasil dibuat dengan mengecek daftar image lokal:
```bash
docker images
```

### Langkah 4: Jalankan Container
Jalankan container dari image yang baru saja kamu build dengan memetakan (*port mapping*) port `5000` host ke port `5000` container:
```bash
docker run -d -p 5000:5000 --name my-inspector node-inspector:1.0
```
Cek status container:
```bash
docker ps
```

### Langkah 5: Pengujian & Verifikasi
Uji apakah aplikasi berjalan dengan baik di dalam container dari terminal Ubuntu VM:
```bash
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/info
```
*(Opsional: Jika menggunakan Host-Only / Bridged Adapter atau Port Forwarding di VirtualBox, kamu juga bisa mengakses `http://<IP-UBUNTU-VM>:5000/info` langsung melalui browser di Windows).*

### Langkah 6: Bersihkan Container Uji Coba
Setelah selesai menguji dan memastikan semuanya berjalan lancar:
```bash
docker stop my-inspector
docker rm my-inspector
```

---

## 4. Goals Project-1 (Kriteria Keberhasilan)

Project-1 dinyatakan **berhasil** apabila kamu sudah mencapai semua poin berikut:

- [ ] **Image Terbangun Tanpa Error:** Perintah `docker build` selesai dengan sukses menggunakan seluruh instruksi (`FROM`, `WORKDIR`, `COPY`, `RUN`, `EXPOSE`, `CMD`).
- [ ] **Container Berjalan Stabil:** Container berstatus `Up` pada output `docker ps` dan tidak langsung *exit*.
- [ ] **Port Mapping Berfungsi:** Endpoint `/`, `/health`, dan `/info` dapat diakses melalui port `5000` dan mengembalikan respons JSON HTTP `200 OK`.
- [ ] **Verifikasi Lingkungan Container:** Pada output JSON `/info`, nilai `working_directory` sesuai dengan path yang kamu tentukan di `WORKDIR` (misalnya `/app`), dan `container_hostname` menampilkan ID unik container.
- [ ] **Dokumentasi Portofolio Siap:** File `README.md` telah kamu perbarui dengan penjelasan project, tujuan, detail konfigurasi `Dockerfile`, serta cara menjalankan aplikasinya untuk di-push ke repositori GitHub kamu.
