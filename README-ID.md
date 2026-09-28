# Assault Fire Server Emulator

**Bahasa:** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | [简体中文](README-ZH-CN.md) | [Bahasa lainnya](README-LANGUAGES.md)

Proyek tidak resmi untuk pelestarian **Assault Fire PH** dan emulasi servernya. Proyek ini dan server yang dijalankan pihak ketiga tidak berafiliasi dengan, disponsori, atau didukung oleh Tencent, Level Up! Games, maupun pemegang hak asli. Server komunitas berjalan secara independen.

> **Versi yang didukung dan diuji hanya:** Assault Fire PH **v1.0.0.24**. Repositori ini tidak menyertakan file game. Anda harus memiliki file game sendiri.

## Cara termudah untuk mulai

1. Letakkan seluruh folder `af-emulator` di dalam folder game Assault Fire PH.
2. Klik kanan `START_ASSAULT_FIRE.ps1`, lalu pilih **Run with PowerShell**. Izinkan akses Administrator jika Windows memintanya.
3. Launcher memeriksa versi dan konfigurasi, menyiapkan kunci lokal, lalu menjalankan server, helper peluncuran, dan klien game.
4. Login di klien. Saat tombol **START** muncul, klik untuk melanjutkan.

Dalam alur satu klik normal, Anda tidak perlu menjalankan server atau alat patch secara manual. Skrip tidak mengunduh atau membagikan file game; skrip hanya menggunakan file lokal milik Anda. Jika versi tidak cocok atau tanda tangan `TGame.exe` atau `TCLS.dll` tidak dapat diverifikasi, berhenti dan jangan memaksakan patch. Sebelum game dijalankan, launcher memasang patch tanggal/waktu terverifikasi secara permanen pada `TGame.exe` setelah membuat cadangan identik bernama `TGame.exe.bak`. Jika tidak ada ruang kode aman, launcher menambahkan bagian PE kecil yang dapat dieksekusi bernama `.afdt` hanya jika tabel bagian memiliki slot kosong; jika tidak, file tidak diubah.

## Setup manual dan pengembangan

Baca [panduan lengkap berbahasa Inggris](README.md) untuk semua langkah dan perintah yang tepat. Anda memerlukan Windows, Python 3.10 atau lebih baru, serta salinan sendiri dari versi game yang didukung. Pada setup manual, tunggu sampai preflight menampilkan `UNLOCKED`. Jika menjalankan game secara manual, jangan klik **START** sebelum helper menampilkan `TCLS ARMED`. Opsi `--server-only` hanya untuk hosting dan tidak membuka gerbang peluncuran game lokal.

## Status dan bantuan

Baseline stabil publik saat ini adalah **v143b**. Jalur VERSION, AUTH, DIR, ROLE, dan ZONE, pengelolaan room, serta alur pertandingan PvE berfungsi. Pembuatan nickname/akun pertama kali dan sebagian fitur sosial/progres masih dikerjakan. Sinkronisasi awal AP pada klien masih memakai solusi lokal sementara.

Saat meminta bantuan, kirim tangkapan layar error, langkah yang sedang dilakukan, perintah persis yang dijalankan, `server/af_server_live.log`, dan versi game. **Jangan kirim** `PRIVATE.PEM`, kata sandi, kredensial akun, token, atau file game asli.

- [Status proyek](docs/STATUS.md) · [Masalah launcher](docs/LAUNCHER_ERRORS.md) · [Catatan setup](docs/VITAL_SETUP_NOTES.md) · [Indeks dokumentasi](docs/README.md)
- [Semua README menurut bahasa](README-LANGUAGES.md)

**Lisensi:** MIT.
