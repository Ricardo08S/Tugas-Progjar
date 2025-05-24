# Tugas 3

**Penjelasan File:**

*   `files/`: Direktori ini berfungsi sebagai penyimpanan untuk semua file yang dikelola oleh server. Ketika client mengunggah file, file tersebut akan disimpan di sini. File yang di-download oleh client juga diambil dari direktori ini.
*   `file_client_cli.py`: Skrip Python ini adalah aplikasi sisi client yang menyediakan antarmuka command-line (CLI) untuk berinteraksi dengan file server. Client ini mampu mengirimkan perintah `LIST`, `GET`, `UPLOAD`, dan `DELETE`.
*   `file_interface.py`: Kelas di dalam file ini berfungsi sebagai antarmuka antara logika server dan operasi sistem file. Ini berisi implementasi metode untuk mendaftar file, mendapatkan konten file, mengunggah file (termasuk decoding Base64), dan menghapus file di direktori `files/`.
*   `file_protocol.py`: File ini mendefinisikan protokol komunikasi antara client dan server. Kelas `FileProtocol` bertanggung jawab untuk mem-parsing string perintah yang diterima dari client, merutekan perintah tersebut ke metode yang sesuai di `file_interface.py`, dan mengembalikan respons dalam format JSON. File ini juga telah diperbarui untuk menangani parsing data Base64 dengan benar.
*   `file_server.py`: Ini adalah skrip utama untuk sisi server. Server mendengarkan koneksi client pada port yang ditentukan (6667) dan menggunakan threading untuk menangani banyak client secara bersamaan. Ia menerima perintah dari client, meneruskannya ke `file_protocol` untuk diproses, dan mengirimkan respons kembali.
*   `PROTOKOL.txt`: Dokumen teks ini berisi spesifikasi lengkap dari protokol komunikasi yang digunakan oleh sistem file server, termasuk definisi untuk perintah `LIST`, `GET`, `UPLOAD`, dan `DELETE`, beserta format parameter dan responsnya.
*   `README.md`: Dokumen ini (yang sedang Anda baca) menjelaskan tentang proyek, struktur file, dan cara menjalankan aplikasi.

## Cara Menjalankan Aplikasi

Ikuti langkah-langkah di bawah untuk menjalankan server dan client:

### Prasyarat

*   Python 3.x terinstal.

### Langkah-langkah

1.  **Navigasi ke Direktori Proyek:**
    Buka terminal atau command prompt, lalu navigasikan ke direktori `Task-3`.

    ```bash
    cd path/to/Task-3
    ```

2.  **Menjalankan File Server:**
    Pada **terminal pertama**, jalankan skrip server. Server akan mendengarkan koneksi pada port `6667`.

    ```bash
    python file_server.py
    ```
    Anda akan melihat log yang menunjukkan server berjalan.

3.  **Menjalankan File Client CLI:**
    Pada **terminal kedua**, jalankan skrip client. Client akan menampilkan prompt interaktif.

    ```bash
    python file_client_cli.py
    ```
    Anda akan melihat pesan selamat datang dan daftar perintah yang tersedia.

### Perintah Client yang Tersedia

Setelah client berjalan, Anda dapat menggunakan perintah-perintah berikut pada prompt `>>>`:

*   `list`: Menampilkan daftar semua file yang tersedia di server.
*   `get <remote_filename>`: Mengunduh file dengan `<remote_filename>` dari server dan menyimpannya di direktori lokal client.
    *   Contoh: `get donalbebek.jpg`
*   `upload <local_filepath> <remote_filename>`: Mengunggah file dari lokasi lokal (`<local_filepath>`) ke server dengan nama `<remote_filename>`. Konten file akan di-encode Base64 secara otomatis oleh client sebelum dikirim.
    *   **Catatan:** `<local_filepath>` harus berupa path relatif terhadap direktori tempat Anda menjalankan `file_client_cli.py`.
    *   Contoh: Untuk mengunggah `my_photo.jpg` yang ada di direktori `Task-3/` ke server dengan nama `new_photo.jpg`: `upload my_photo.jpg new_photo.jpg`
*   `delete <remote_filename>`: Menghapus file dengan `<remote_filename>` dari server.
    *   Contoh: `delete new_photo.jpg`
*   `exit`: Keluar dari aplikasi client.

---