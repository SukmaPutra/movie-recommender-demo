# ReelExplain

Demo sidang untuk sistem rekomendasi film FunkSVD dengan penjelasan post-hoc berbasis aturan. Aplikasi membaca hasil eksperimen yang sudah diekspor. Model tidak dilatih ulang saat aplikasi berjalan.

## Menjalankan di Windows

Dari folder `movie-recommender-demo`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Buka alamat yang muncul di terminal, biasanya `http://localhost:8501`.

Jika PowerShell menolak skrip aktivasi, jalankan `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` pada jendela itu, lalu ulangi aktivasi.

## Isi data

`data/demo_data.csv` memuat 59.810 rekomendasi (5.981 pengguna, masing-masing 10 film). Kolom asli adalah `UserID`, `Peringkat`, `Judul`, `Evidence`, dan `Penjelasan`. Kolom `Genre` dan `SkorPrediksi` digabung dari ekspor film dan Top-10 penelitian. Skor adalah `est_clipped`, bukan hasil hitung baru.

Label evidence yang sah: `Genre Preference`, `Genre Frequency`, `Item Quality`, `Recent Preference`, `Fallback generik`.

## Deploy ke Streamlit Community Cloud

1. Buat repository GitHub **publik**.
2. Unggah isi folder `movie-recommender-demo`, termasuk `app.py`, `requirements.txt`, `.streamlit/config.toml`, dan `data/demo_data.csv`.
3. Jangan unggah notebook, faktor laten, atau riwayat uji.
4. Di [share.streamlit.io](https://share.streamlit.io), pilih repository, branch, dan entry point `app.py`.
5. Deploy, lalu salin URL publik untuk sidang.

Tidak perlu secrets, API key, atau GPU.

## Jika deploy gagal

- **Dataset tidak ditemukan:** pastikan `data/demo_data.csv` ikut ter-commit dan path aplikasi tetap relatif terhadap `app.py`.
- **Dependency gagal:** biarkan `requirements.txt` hanya berisi Streamlit dan Pandas dengan versi yang sudah ditulis.
- **Aplikasi kosong atau error kolom:** jangan mengganti isi CSV. Jumlah baris harus 59.810 dan tiap pengguna harus punya peringkat 1 sampai 10.
- **Repository tidak muncul:** Streamlit Community Cloud membutuhkan repository publik, atau akses GitHub yang sudah diotorisasi ke repository privat.
