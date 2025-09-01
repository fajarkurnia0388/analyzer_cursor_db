# 📊 Database Analyzer Scripts

[![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0-orange.svg)]()

Koleksi script Python untuk menganalisis dan mengkonversi database SQLite, khususnya file `state.vscdb` dari aplikasi Cursor/VS Code.

> **🚀 Quick Start:** Jalankan `python advanced_analyzer.py --quick` untuk analisis cepat!

## 🌐 Versi Bahasa

- 🇺🇸 [English](README.md)
- 🇮🇩 [Bahasa Indonesia](README_ID.md) (Current)

## 📁 Struktur Project

```
analyzer/
├── 📄 advanced_analyzer.py          # Analisis kata kunci advanced dengan output terstruktur
├── 📄 cursor_analyzer.py            # Analisis khusus kata kunci "cursor"
├── 📄 keyword_analyzer_optimized.py # Analisis kata kunci dengan performa tinggi
├── 📄 keyword_analyzer.py           # Analisis kata kunci dasar
├── 📄 state_vscdb_converter.py      # Konversi database lengkap ke format readable
├── 📄 test_syntax.py                # Test syntax untuk script
├── 📁 analysis_output_*/            # Output folder analisis
├── 📁 state_converted_*/            # Output folder konversi database
└── 📁 output_old/                   # Output lama
```

## 🚀 Script Overview

### 1. **advanced_analyzer.py** - Analisis Kata Kunci Advanced

**Fitur Utama:**

- Analisis kata kunci dengan output terstruktur dalam folder
- Kategorisasi otomatis: authentication, subscription, ai_features, account_status, blackbox_specific, usage_limits
- Deteksi tingkat sensitivitas data (high/medium/low)
- Sensor data sensitif otomatis
- Laporan HTML dan security report
- Mode quick untuk performa tinggi

**Target Kata Kunci:**

- 🔐 **Authentication**: token, auth, credential, password, session
- 💳 **Subscription**: pro, plan, subscription, trial, premium, billing
- 🤖 **AI Features**: max mode, ai, model, chat, composer, copilot
- 👤 **Account Status**: status, active, enabled, disabled, banned
- ⚫ **Blackbox Specific**: blackbox, blackboxai, blackboxapp
- 📊 **Usage Limits**: limit, quota, usage, remaining, consumed

**Cara Penggunaan:**

```bash
# Mode normal
python advanced_analyzer.py

# Mode quick (maksimal 1000 items)
python advanced_analyzer.py --quick

# Dengan path database custom
python advanced_analyzer.py /path/to/state.vscdb

# Kombinasi
python advanced_analyzer.py /path/to/state.vscdb --quick
```

**Output:**

```
analysis_output_YYYYMMDD_HHMMSS/
├── 📁 authentication/
│   ├── 📄 authentication_results.json
│   └── 📄 authentication_summary.txt
├── 📁 subscription/
├── 📁 ai_features/
├── 📁 account_status/
├── 📁 blackbox_specific/
├── 📁 usage_limits/
├── 📁 summary/
│   └── 📄 overall_summary.json
├── 📁 reports/
│   ├── 📄 detailed_report.html
│   └── 📄 security_report.txt
└── 📄 tree_structure.txt
```

---

### 2. **cursor_analyzer.py** - Analisis Khusus "Cursor"

**Fitur Utama:**

- Fokus pada kata kunci "cursor" dan konteksnya
- Kategorisasi berdasarkan konteks: settings, ui, editor, extension, history, theme, dll
- Analisis pattern penggunaan kata "cursor"
- Export hasil ke JSON dengan struktur detail

**Kategori Konteks:**

- ⚙️ **Settings**: setting, config, preference, option
- 🖥️ **UI**: workbench, view, panel, sidebar, explorer
- 📝 **Editor**: editor, text, file, document
- 🔌 **Extension**: extension, plugin, addon
- 📚 **History**: history, recent, opened, path
- 🎨 **Theme**: theme, color, appearance
- ⌨️ **Key Binding**: keybinding, shortcut, key
- 🪟 **Window**: window, layout, position

**Cara Penggunaan:**

```bash
python cursor_analyzer.py
python cursor_analyzer.py /path/to/state.vscdb
```

**Output:**

- File JSON dengan hasil analisis lengkap
- Laporan ringkasan di console
- Kategorisasi otomatis berdasarkan konteks

---

### 3. **keyword_analyzer_optimized.py** - Analisis Performa Tinggi

**Fitur Utama:**

- Optimasi performa dengan batching dan caching
- Progress tracking real-time
- Query optimization dengan SQLite PRAGMA
- Export dengan opsi sensor data sensitif
- Analisis komprehensif dengan statistik detail

**Optimasi Performa:**

- Batch processing untuk menghindari memory issues
- Query cache untuk menghindari query berulang
- SQLite optimizations (WAL mode, cache size, temp store)
- Progress indicator untuk dataset besar

**Cara Penggunaan:**

```bash
# Default batch size 500
python keyword_analyzer_optimized.py

# Custom batch size
python keyword_analyzer_optimized.py --batch-size=1000

# Dengan path database
python keyword_analyzer_optimized.py /path/to/state.vscdb --batch-size=200
```

**Output:**

- File JSON komprehensif dengan semua hasil
- Statistik performa dan timing
- Opsi export dengan/tanpa data sensitif

---

### 4. **keyword_analyzer.py** - Analisis Kata Kunci Dasar

**Fitur Utama:**

- Analisis kata kunci dengan mode quick dan full
- Pattern analysis dengan regex
- Extract informasi kredensial
- Security report dengan rekomendasi
- Export dengan opsi sensor data

**Mode Analisis:**

- ⚡ **Quick Mode**: ~30 detik, maksimal 1000 items
- 🔍 **Full Mode**: beberapa menit, semua data

**Cara Penggunaan:**

```bash
# Mode interaktif (pilih quick/full)
python keyword_analyzer.py

# Mode quick langsung
python keyword_analyzer.py --quick

# Dengan path database
python keyword_analyzer.py /path/to/state.vscdb --quick
```

**Output:**

- Laporan detail di console
- Security report dengan rekomendasi
- File JSON dengan hasil analisis

---

### 5. **state_vscdb_converter.py** - Konversi Database Lengkap

**Fitur Utama:**

- Konversi seluruh isi database ke format readable
- Export setiap tabel ke file JSON terpisah
- Schema export untuk setiap tabel
- Summary file untuk setiap tabel
- Laporan HTML untuk navigasi
- Processing data binary dan JSON

**Cara Penggunaan:**

```bash
python state_vscdb_converter.py
python state_vscdb_converter.py /path/to/state.vscdb
```

**Output:**

```
state_converted_YYYYMMDD_HHMMSS/
├── 📁 TableName1/
│   ├── 📄 TableName1_data.json
│   ├── 📄 TableName1_schema.json
│   └── 📄 TableName1_summary.txt
├── 📁 TableName2/
├── 📁 summary/
│   └── 📄 database_summary.json
├── 📁 reports/
│   └── 📄 export_report.html
```

---

### 6. **test_syntax.py** - Test Syntax

**Fitur Utama:**

- Test syntax untuk script advanced_analyzer.py
- Validasi kode sebelum eksekusi
- Error reporting yang detail

**Cara Penggunaan:**

```bash
python test_syntax.py
```

---

## 🛠️ Requirements

**Python Dependencies:**

- Python 3.6+
- sqlite3 (built-in)
- json (built-in)
- os, sys, datetime, collections, re, pathlib (built-in)
- base64 (built-in)

**Tidak memerlukan instalasi package eksternal!**

## 📋 Cara Penggunaan Umum

### 1. Persiapan

```bash
# Clone atau download script
# Pastikan file state.vscdb ada di direktori yang sama
```

### 2. Analisis Cepat

```bash
# Untuk analisis cepat dengan hasil terstruktur
python advanced_analyzer.py --quick

# Untuk analisis performa tinggi
python keyword_analyzer_optimized.py --batch-size=500
```

### 3. Analisis Lengkap

```bash
# Untuk analisis lengkap dengan output terstruktur
python advanced_analyzer.py

# Untuk konversi database lengkap
python state_vscdb_converter.py
```

### 4. Analisis Spesifik

```bash
# Untuk analisis khusus kata "cursor"
python cursor_analyzer.py

# Untuk analisis kata kunci dengan mode interaktif
python keyword_analyzer.py
```

## 🔒 Keamanan Data

**Fitur Keamanan:**

- ✅ Deteksi otomatis data sensitif
- ✅ Sensor data kredensial dan token
- ✅ Kategorisasi tingkat sensitivitas
- ✅ Opsi export dengan/tanpa data sensitif
- ✅ Security report dengan rekomendasi

**Tingkat Sensitivitas:**

- 🔴 **High**: token, password, key, secret, credential
- 🟡 **Medium**: userid, email, api, auth
- 🟢 **Low**: plan, status, mode, feature

## 📊 Output dan Laporan

### Format Output:

- **JSON**: Data terstruktur untuk analisis lebih lanjut
- **HTML**: Laporan visual yang mudah dibaca
- **TXT**: Summary dan laporan keamanan
- **Tree Structure**: Navigasi file output

### Jenis Laporan:

1. **Overall Summary**: Statistik keseluruhan analisis
2. **Security Report**: Laporan keamanan dengan rekomendasi
3. **Category Breakdown**: Distribusi per kategori
4. **Detailed Results**: Hasil detail dengan konteks
5. **Export Report**: Laporan navigasi file output

## ⚡ Tips Performa

### Untuk Database Besar (>100MB):

```bash
# Gunakan mode quick
python advanced_analyzer.py --quick

# Atau gunakan batch size kecil
python keyword_analyzer_optimized.py --batch-size=200
```

### Untuk Analisis Lengkap:

```bash
# Gunakan script optimized untuk performa terbaik
python keyword_analyzer_optimized.py --batch-size=500
```

## 🐛 Troubleshooting

### Error Umum:

**1. File tidak ditemukan:**

```
❌ [ERROR] File state.vscdb tidak ditemukan!
💡 [SOLUTION] Copy file state.vscdb ke direktori script ini
```

**2. Database locked:**

```
❌ [ERROR] Database is locked
💡 [SOLUTION] Tutup aplikasi Cursor/VS Code terlebih dahulu
```

**3. Memory error:**

```
❌ [ERROR] Out of memory
💡 [SOLUTION] Gunakan mode quick atau batch size lebih kecil
```

## 📝 Contoh Output

### Console Output:

```
🎯 [ADVANCED ANALYZER] Script Analisis Kata Kunci Advanced
============================================================
🔍 Target: token, max mode, kredensial, status akun, pro plan, pro trial
============================================================
✅ [SUCCESS] Berhasil terhubung ke database: state.vscdb
📊 [INFO] Ukuran file: 45,234,567 bytes (43.15 MB)
📋 [INFO] Menganalisa 3 tabel: ItemTable, cursorDiskKV, ExtensionState

🔍 [TABLE] Menganalisa tabel: ItemTable
   ✅ Ditemukan 1,234 hasil

📊 [SUMMARY] Total ditemukan: 1,234 referensi kata kunci
   📁 Authentication: 456 item
   📁 Subscription: 234 item
   📁 Ai Features: 123 item
   📁 Account Status: 89 item
   📁 Blackbox Specific: 67 item
   📁 Usage Limits: 45 item

🎉 [COMPLETED] Analisis selesai!
📁 Output tersimpan di: analysis_output_20250902_042747
🌐 Buka laporan HTML: analysis_output_20250902_042747/reports/detailed_report.html
```

## 🤝 Kontribusi

Script ini dibuat untuk analisis database Cursor/VS Code. Jika ada bug atau fitur yang ingin ditambahkan, silakan buat issue atau pull request.

## 📄 Lisensi

Script ini dibuat untuk keperluan analisis dan debugging. Gunakan dengan bijak dan pastikan data sensitif tetap aman.

---

**💡 Tips:** Mulai dengan `advanced_analyzer.py --quick` untuk analisis cepat, kemudian gunakan script lain sesuai kebutuhan spesifik Anda.
