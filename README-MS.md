# Assault Fire Server Emulator

**Bahasa:** [English](README.md) | [Tagalog](README-TL.md) | [Cebuano](README-CEB.md) | [简体中文](README-ZH-CN.md) | [Bahasa lain](README-LANGUAGES.md)

Projek tidak rasmi untuk memelihara **Assault Fire PH** dan meniru pelayan permainannya. Projek ini dan pelayan pihak ketiga tidak berafiliasi dengan, ditaja atau disokong oleh Tencent, Level Up! Games atau pemilik hak asal. Pelayan komuniti dikendalikan secara bebas.

> **Versi yang disokong dan diuji sahaja:** Assault Fire PH **v1.0.0.24**. Repositori ini tidak menyertakan fail permainan. Anda perlu memiliki fail permainan sendiri.

## Cara paling mudah untuk bermula

1. Letakkan seluruh folder `af-emulator` di dalam folder permainan Assault Fire PH.
2. Klik kanan `START_ASSAULT_FIRE.ps1`, kemudian pilih **Run with PowerShell**. Benarkan akses Administrator jika diminta oleh Windows.
3. Pelancar menyemak versi dan konfigurasi, menyediakan kunci setempat, kemudian memulakan pelayan, pembantu pelancaran dan klien permainan.
4. Log masuk ke klien. Apabila butang **START** muncul, klik untuk meneruskan.

Dengan aliran satu klik biasa, anda tidak perlu memulakan pelayan atau alat patch secara manual. Skrip tidak memuat turun atau mengedarkan fail permainan; ia hanya menggunakan fail setempat anda. Jika versi tidak sepadan atau tandatangan `TGame.exe` atau `TCLS.dll` tidak dapat disahkan, berhenti dan jangan paksa patch. Sebelum permainan dimulakan, pelancar memasang patch tarikh/masa yang disahkan secara kekal pada `TGame.exe` selepas menyimpan sandaran sepadan bernama `TGame.exe.bak`. Jika tiada ruang kod selamat, pelancar menambah seksyen PE boleh laksana kecil `.afdt` hanya jika pengepala PE mempunyai slot seksyen kosong; jika tiada, fail tidak diubah.

## Persediaan manual dan pembangun

Rujuk [panduan lengkap dalam bahasa Inggeris](README.md) untuk semua langkah dan arahan tepat. Anda perlukan Windows, Python 3.10 atau lebih baharu dan salinan sendiri bagi versi permainan yang disokong. Dalam persediaan manual, tunggu sehingga preflight menunjukkan `UNLOCKED`. Jika memulakan permainan secara manual, jangan klik **START** sebelum pembantu memaparkan `TCLS ARMED`. Pilihan `--server-only` hanya untuk hosting dan tidak membuka gerbang pelancaran permainan setempat.

## Status dan bantuan

Baseline stabil awam sekarang ialah **v143b**. Aliran VERSION, AUTH, DIR, ROLE dan ZONE, pengurusan bilik serta perlawanan PvE berfungsi. Penciptaan nama/akaun kali pertama dan beberapa ciri sosial/progres masih dalam pembangunan. Penyegerakan awal AP pada klien masih menggunakan penyelesaian setempat sementara.

Untuk meminta bantuan, hantarkan tangkap layar ralat, langkah yang dilakukan, arahan tepat, `server/af_server_live.log` dan versi permainan. **Jangan hantar** `PRIVATE.PEM`, kata laluan, kelayakan akaun, token atau fail permainan asal.

- [Status projek](docs/STATUS.md) · [Ralat pelancar](docs/LAUNCHER_ERRORS.md) · [Nota persediaan penting](docs/VITAL_SETUP_NOTES.md) · [Indeks dokumentasi](docs/README.md)
- [Semua README mengikut bahasa](README-LANGUAGES.md)

**Lesen:** MIT.
