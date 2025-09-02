#!/usr/bin/env python3
"""
Script Komprehensif untuk Menganalisis dan Membuat Dictionary Kata dari Database state.vscdb
Membuat struktur folder dictionary dengan kategori alfabet dan berbagai format output
Author: AI Assistant
"""

import sqlite3
import json
import os
import sys
import re
import csv
from datetime import datetime
from collections import defaultdict, Counter
from pathlib import Path
import string


class ComprehensiveDictionaryAnalyzer:
    def __init__(self, db_path, output_dir="dictionary_analysis"):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.stats = {
            "total_words": 0,
            "total_phrases": 0,
            "unique_words": 0,
            "unique_phrases": 0,
            "processed_tables": 0,
            "processed_rows": 0,
            "analysis_time": 0,
        }

        # Dictionary untuk menyimpan hasil
        self.word_dictionary = defaultdict(lambda: defaultdict(list))
        self.phrase_dictionary = defaultdict(lambda: defaultdict(list))
        self.word_frequencies = Counter()
        self.phrase_frequencies = Counter()

        # Pattern untuk ekstraksi
        self.word_pattern = re.compile(r"\b[a-zA-Z]{3,}\b")  # Kata minimal 3 huruf
        self.phrase_pattern = re.compile(
            r"\b[a-zA-Z\s]{10,50}\b"
        )  # Frasa 10-50 karakter

        # Kata-kata umum yang akan difilter
        self.common_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "its",
            "may",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "has",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
            "yes",
            "yet",
        }

    def connect(self):
        """Membuat koneksi ke database SQLite"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ [ERROR] File tidak ditemukan: {self.db_path}")
                return False

            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ [SUCCESS] Berhasil terhubung ke database: {self.db_path}")

            file_size = os.path.getsize(self.db_path)
            print(
                f"📊 [INFO] Ukuran file: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)"
            )

            return True
        except Exception as e:
            print(f"❌ [ERROR] Gagal terhubung: {e}")
            return False

    def close(self):
        """Menutup koneksi database"""
        if self.conn:
            self.conn.close()

    def get_tables(self):
        """Mendapatkan daftar semua tabel dalam database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in cursor.fetchall()]

    def create_dictionary_structure(self):
        """Membuat struktur folder dictionary"""
        print(f"\n📁 [CREATE STRUCTURE] Membuat struktur folder dictionary...")

        # Buat folder utama
        self.output_dir.mkdir(exist_ok=True)

        # Buat subfolder untuk setiap huruf alfabet
        for letter in string.ascii_uppercase:
            letter_dir = self.output_dir / letter
            letter_dir.mkdir(exist_ok=True)

            # Buat subfolder untuk words dan phrases
            (letter_dir / "words").mkdir(exist_ok=True)
            (letter_dir / "phrases").mkdir(exist_ok=True)

        # Buat folder untuk statistik dan laporan
        (self.output_dir / "statistics").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)

        print(f"✅ [SUCCESS] Struktur folder dictionary dibuat di: {self.output_dir}")

    def extract_text_content(self):
        """Mengekstrak semua konten teks dari database"""
        print(f"\n🔍 [EXTRACT] Mengekstrak konten teks dari database...")

        tables = self.get_tables()
        total_tables = len(tables)
        processed_tables = 0

        for table_name in tables:
            print(
                f"📋 [TABLE] Memproses tabel: {table_name} ({processed_tables + 1}/{total_tables})"
            )

            try:
                cursor = self.conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()

                # Dapatkan nama kolom
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]

                # Proses setiap baris
                for row in rows:
                    self._process_row(row, columns, table_name)
                    self.stats["processed_rows"] += 1

                processed_tables += 1
                self.stats["processed_tables"] = processed_tables

                print(f"   ✅ Diproses {len(rows)} baris dari tabel {table_name}")

            except Exception as e:
                print(f"   ⚠️ Error memproses tabel {table_name}: {e}")

        print(f"\n📊 [SUMMARY] Ekstraksi selesai:")
        print(f"   📋 Tabel diproses: {self.stats['processed_tables']}")
        print(f"   📄 Baris diproses: {self.stats['processed_rows']:,}")

    def _process_row(self, row, columns, table_name):
        """Memproses satu baris data"""
        for col, value in zip(columns, row):
            if value is None:
                continue

            # Konversi ke string
            text_content = str(value)

            # Ekstrak kata-kata
            self._extract_words(text_content, table_name, col)

            # Ekstrak frasa
            self._extract_phrases(text_content, table_name, col)

    def _extract_words(self, text, table_name, column_name):
        """Mengekstrak kata-kata individual dari teks"""
        words = self.word_pattern.findall(text.lower())

        for word in words:
            # Filter kata-kata umum
            if word in self.common_words:
                continue

            # Dapatkan huruf pertama
            first_letter = word[0].upper()

            # Simpan ke dictionary
            word_entry = {
                "word": word,
                "table": table_name,
                "column": column_name,
                "context": text[:100] + "..." if len(text) > 100 else text,
                "timestamp": datetime.now().isoformat(),
            }

            self.word_dictionary[first_letter][word].append(word_entry)
            self.word_frequencies[word] += 1
            self.stats["total_words"] += 1

    def _extract_phrases(self, text, table_name, column_name):
        """Mengekstrak frasa bermakna dari teks"""
        # Cari frasa yang mengandung kata-kata bermakna
        phrases = self.phrase_pattern.findall(text)

        for phrase in phrases:
            # Bersihkan dan normalisasi
            clean_phrase = re.sub(r"\s+", " ", phrase.strip().lower())

            # Pastikan frasa memiliki minimal 2 kata
            if len(clean_phrase.split()) < 2:
                continue

            # Dapatkan huruf pertama
            first_letter = clean_phrase[0].upper()

            # Simpan ke dictionary
            phrase_entry = {
                "phrase": clean_phrase,
                "table": table_name,
                "column": column_name,
                "context": text[:150] + "..." if len(text) > 150 else text,
                "word_count": len(clean_phrase.split()),
                "timestamp": datetime.now().isoformat(),
            }

            self.phrase_dictionary[first_letter][clean_phrase].append(phrase_entry)
            self.phrase_frequencies[clean_phrase] += 1
            self.stats["total_phrases"] += 1

    def save_dictionary_files(self):
        """Menyimpan hasil dictionary ke file"""
        print(f"\n💾 [SAVE] Menyimpan hasil dictionary ke file...")

        # Simpan words
        self._save_words()

        # Simpan phrases
        self._save_phrases()

        print(f"✅ [SUCCESS] Semua file dictionary berhasil disimpan")

    def _save_words(self):
        """Menyimpan kata-kata ke file"""
        print(f"   📝 Menyimpan {self.stats['total_words']:,} kata-kata...")

        for letter in string.ascii_uppercase:
            if letter not in self.word_dictionary:
                continue

            letter_dir = self.output_dir / letter / "words"

            # Simpan sebagai JSON
            json_file = letter_dir / f"{letter}_words.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(
                    dict(self.word_dictionary[letter]), f, indent=2, ensure_ascii=False
                )

            # Simpan sebagai TXT
            txt_file = letter_dir / f"{letter}_words.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(f"DICTIONARY WORDS - LETTER {letter}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total words: {len(self.word_dictionary[letter])}\n")
                f.write(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                for word, entries in sorted(self.word_dictionary[letter].items()):
                    frequency = len(entries)
                    f.write(f"📝 {word} ({frequency} occurrences)\n")
                    f.write("-" * 40 + "\n")

                    # Tampilkan beberapa contoh konteks
                    for i, entry in enumerate(entries[:3]):  # Maksimal 3 contoh
                        f.write(f"   {i+1}. Table: {entry['table']}\n")
                        f.write(f"      Context: {entry['context'][:80]}...\n")

                    if len(entries) > 3:
                        f.write(f"      ... and {len(entries) - 3} more occurrences\n")

                    f.write("\n")

            # Simpan sebagai CSV
            csv_file = letter_dir / f"{letter}_words.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Word", "Frequency", "Table", "Column", "Context"])

                for word, entries in sorted(self.word_dictionary[letter].items()):
                    for entry in entries:
                        writer.writerow(
                            [
                                word,
                                len(entries),
                                entry["table"],
                                entry["column"],
                                entry["context"][:100],
                            ]
                        )

            print(
                f"   📄 {letter}: {len(self.word_dictionary[letter])} words → {letter_dir}"
            )

    def _save_phrases(self):
        """Menyimpan frasa ke file"""
        print(f"   📝 Menyimpan {self.stats['total_phrases']:,} frasa...")

        for letter in string.ascii_uppercase:
            if letter not in self.phrase_dictionary:
                continue

            letter_dir = self.output_dir / letter / "phrases"

            # Simpan sebagai JSON
            json_file = letter_dir / f"{letter}_phrases.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(
                    dict(self.phrase_dictionary[letter]),
                    f,
                    indent=2,
                    ensure_ascii=False,
                )

            # Simpan sebagai TXT
            txt_file = letter_dir / f"{letter}_phrases.txt"
            with open(txt_file, "w", encoding="utf-8") as f:
                f.write(f"DICTIONARY PHRASES - LETTER {letter}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total phrases: {len(self.phrase_dictionary[letter])}\n")
                f.write(
                    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                )

                for phrase, entries in sorted(self.phrase_dictionary[letter].items()):
                    frequency = len(entries)
                    f.write(f"📝 {phrase} ({frequency} occurrences)\n")
                    f.write("-" * 40 + "\n")

                    # Tampilkan beberapa contoh konteks
                    for i, entry in enumerate(entries[:2]):  # Maksimal 2 contoh
                        f.write(f"   {i+1}. Table: {entry['table']}\n")
                        f.write(f"      Words: {entry['word_count']}\n")
                        f.write(f"      Context: {entry['context'][:100]}...\n")

                    if len(entries) > 2:
                        f.write(f"      ... and {len(entries) - 2} more occurrences\n")

                    f.write("\n")

            # Simpan sebagai CSV
            csv_file = letter_dir / f"{letter}_phrases.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    ["Phrase", "Frequency", "Word Count", "Table", "Column", "Context"]
                )

                for phrase, entries in sorted(self.phrase_dictionary[letter].items()):
                    for entry in entries:
                        writer.writerow(
                            [
                                phrase,
                                len(entries),
                                entry["word_count"],
                                entry["table"],
                                entry["column"],
                                entry["context"][:100],
                            ]
                        )

            print(
                f"   📄 {letter}: {len(self.phrase_dictionary[letter])} phrases → {letter_dir}"
            )

    def generate_statistics(self):
        """Membuat statistik komprehensif"""
        print(f"\n📊 [STATISTICS] Membuat statistik komprehensif...")

        stats_dir = self.output_dir / "statistics"

        # Statistik umum
        general_stats = {
            "analysis_info": {
                "database_file": self.db_path,
                "analysis_date": datetime.now().isoformat(),
                "total_tables_processed": self.stats["processed_tables"],
                "total_rows_processed": self.stats["processed_rows"],
            },
            "word_statistics": {
                "total_words": self.stats["total_words"],
                "unique_words": len(self.word_frequencies),
                "most_common_words": dict(self.word_frequencies.most_common(50)),
            },
            "phrase_statistics": {
                "total_phrases": self.stats["total_phrases"],
                "unique_phrases": len(self.phrase_frequencies),
                "most_common_phrases": dict(self.phrase_frequencies.most_common(50)),
            },
            "letter_distribution": {
                "words_by_letter": {
                    letter: len(self.word_dictionary.get(letter, {}))
                    for letter in string.ascii_uppercase
                },
                "phrases_by_letter": {
                    letter: len(self.phrase_dictionary.get(letter, {}))
                    for letter in string.ascii_uppercase
                },
            },
        }

        # Simpan statistik umum
        with open(stats_dir / "general_statistics.json", "w", encoding="utf-8") as f:
            json.dump(general_stats, f, indent=2, ensure_ascii=False)

        # Buat laporan TXT
        with open(stats_dir / "analysis_report.txt", "w", encoding="utf-8") as f:
            f.write("COMPREHENSIVE DICTIONARY ANALYSIS REPORT\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Database: {self.db_path}\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Tables Processed: {self.stats['processed_tables']}\n")
            f.write(f"Rows Processed: {self.stats['processed_rows']:,}\n\n")

            f.write("WORD STATISTICS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Words: {self.stats['total_words']:,}\n")
            f.write(f"Unique Words: {len(self.word_frequencies):,}\n\n")

            f.write("PHRASE STATISTICS:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Phrases: {self.stats['total_phrases']:,}\n")
            f.write(f"Unique Phrases: {len(self.phrase_frequencies):,}\n\n")

            f.write("TOP 20 WORDS:\n")
            f.write("-" * 15 + "\n")
            for word, freq in self.word_frequencies.most_common(20):
                f.write(f"• {word}: {freq:,}\n")

            f.write("\nTOP 20 PHRASES:\n")
            f.write("-" * 16 + "\n")
            for phrase, freq in self.phrase_frequencies.most_common(20):
                f.write(f"• {phrase}: {freq:,}\n")

        print(f"📊 [SUCCESS] Statistik disimpan di: {stats_dir}")

    def create_html_report(self):
        """Membuat laporan HTML navigasi"""
        print(f"\n🌐 [HTML REPORT] Membuat laporan HTML...")

        reports_dir = self.output_dir / "reports"
        html_file = reports_dir / "dictionary_navigation.html"

        html_content = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dictionary Analysis Report - {Path(self.db_path).name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .letter-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(80px, 1fr)); gap: 10px; margin: 20px 0; }}
        .letter-card {{ background: #007bff; color: white; padding: 15px; text-align: center; border-radius: 5px; text-decoration: none; transition: background 0.3s; }}
        .letter-card:hover {{ background: #0056b3; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #007bff; color: white; }}
        .file-link {{ color: #007bff; text-decoration: none; }}
        .file-link:hover {{ text-decoration: underline; }}
        .code {{ font-family: monospace; background: #f8f9fa; padding: 2px 4px; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 Comprehensive Dictionary Analysis Report</h1>
        <p><strong>Database:</strong> {Path(self.db_path).name}</p>
        <p><strong>Analysis Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <h2>📊 Analysis Summary</h2>
            <div class="stats">
                <div class="stat">
                    <h3>{self.stats['total_words']:,}</h3>
                    <p>Total Words</p>
                </div>
                <div class="stat">
                    <h3>{len(self.word_frequencies):,}</h3>
                    <p>Unique Words</p>
                </div>
                <div class="stat">
                    <h3>{self.stats['total_phrases']:,}</h3>
                    <p>Total Phrases</p>
                </div>
                <div class="stat">
                    <h3>{len(self.phrase_frequencies):,}</h3>
                    <p>Unique Phrases</p>
                </div>
            </div>
        </div>

        <h2>🔤 Letter Categories</h2>
        <div class="letter-grid">
"""

        # Tambahkan grid huruf
        for letter in string.ascii_uppercase:
            word_count = len(self.word_dictionary.get(letter, {}))
            phrase_count = len(self.phrase_dictionary.get(letter, {}))
            total_count = word_count + phrase_count

            if total_count > 0:
                html_content += f"""
            <a href="#{letter}" class="letter-card">
                <div style="font-size: 24px; font-weight: bold;">{letter}</div>
                <div style="font-size: 12px;">{total_count} items</div>
            </a>
"""

        html_content += """
        </div>

        <h2>📋 Detailed Breakdown</h2>
        <table>
            <tr>
                <th>Letter</th>
                <th>Words</th>
                <th>Phrases</th>
                <th>Total</th>
                <th>Files</th>
            </tr>
"""

        for letter in string.ascii_uppercase:
            word_count = len(self.word_dictionary.get(letter, {}))
            phrase_count = len(self.phrase_dictionary.get(letter, {}))
            total_count = word_count + phrase_count

            if total_count > 0:
                files = []
                if word_count > 0:
                    files.extend(
                        [
                            f"{letter}/words/{letter}_words.json",
                            f"{letter}/words/{letter}_words.txt",
                            f"{letter}/words/{letter}_words.csv",
                        ]
                    )
                if phrase_count > 0:
                    files.extend(
                        [
                            f"{letter}/phrases/{letter}_phrases.json",
                            f"{letter}/phrases/{letter}_phrases.txt",
                            f"{letter}/phrases/{letter}_phrases.csv",
                        ]
                    )

                html_content += f"""
            <tr id="{letter}">
                <td><strong>{letter}</strong></td>
                <td>{word_count:,}</td>
                <td>{phrase_count:,}</td>
                <td>{total_count:,}</td>
                <td>
"""

                for file in files[:3]:  # Tampilkan maksimal 3 file
                    html_content += f'<a href="{file}" class="file-link">📄 {Path(file).name}</a><br>'

                if len(files) > 3:
                    html_content += f"... and {len(files) - 3} more files"

                html_content += "</td></tr>"

        html_content += """
        </table>

        <h2>📁 File Structure</h2>
        <div style="font-family: monospace; background: #f8f9fa; padding: 15px; border-radius: 5px;">
"""

        # Buat struktur tree
        tree_content = f"""📁 {self.output_dir.name}/
├── 📁 statistics/
│   ├── 📄 general_statistics.json
│   └── 📄 analysis_report.txt
├── 📁 reports/
│   └── 📄 dictionary_navigation.html"""

        for letter in string.ascii_uppercase:
            if letter in self.word_dictionary or letter in self.phrase_dictionary:
                tree_content += f"""
├── 📁 {letter}/
│   ├── 📁 words/
│   │   ├── 📄 {letter}_words.json
│   │   ├── 📄 {letter}_words.txt
│   │   └── 📄 {letter}_words.csv
│   └── 📁 phrases/
│       ├── 📄 {letter}_phrases.json
│       ├── 📄 {letter}_phrases.txt
│       └── 📄 {letter}_phrases.csv"""

        html_content += f"<pre>{tree_content}</pre>"
        html_content += """
        </div>

        <h2>💡 Usage Instructions</h2>
        <ul>
            <li><strong>Navigation:</strong> Click on letter cards above to jump to that section</li>
            <li><strong>Files:</strong> Click on file links to open the corresponding data files</li>
            <li><strong>Formats:</strong> Each category has JSON, TXT, and CSV formats available</li>
            <li><strong>Statistics:</strong> Check the statistics folder for detailed analysis reports</li>
        </ul>
    </div>
</body>
</html>
"""

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"🌐 [SUCCESS] Laporan HTML dibuat: {html_file}")

    def run_comprehensive_analysis(self):
        """Menjalankan analisis komprehensif lengkap"""
        print("🎯 [COMPREHENSIVE DICTIONARY ANALYZER] Analisis Dictionary Lengkap")
        print("=" * 80)
        print("🔍 Menganalisis semua kata dan frasa yang dapat dideteksi")
        print("📁 Membuat struktur folder dictionary dengan kategori alfabet")
        print("=" * 80)

        start_time = datetime.now()

        if not self.connect():
            return False

        try:
            # 1. Buat struktur folder
            self.create_dictionary_structure()

            # 2. Ekstrak konten teks
            self.extract_text_content()

            # 3. Simpan file dictionary
            self.save_dictionary_files()

            # 4. Generate statistik
            self.generate_statistics()

            # 5. Buat laporan HTML
            self.create_html_report()

            # Hitung waktu eksekusi
            end_time = datetime.now()
            execution_time = end_time - start_time
            self.stats["analysis_time"] = execution_time.total_seconds()

            print("\n🎉 [COMPLETED] Analisis dictionary lengkap selesai!")
            print(f"⏱️  Waktu eksekusi: {execution_time}")
            print(f"📁 Output tersimpan di: {self.output_dir}")
            print(f"📊 Total kata: {self.stats['total_words']:,}")
            print(f"📝 Total frasa: {self.stats['total_phrases']:,}")
            print(
                f"🌐 Buka laporan: {self.output_dir}/reports/dictionary_navigation.html"
            )

        except Exception as e:
            print(f"❌ [ERROR] Terjadi kesalahan: {e}")
            import traceback

            traceback.print_exc()
            return False

        finally:
            self.close()

        return True


def main():
    print(
        "🚀 [COMPREHENSIVE DICTIONARY ANALYZER] Script Analisis Dictionary Komprehensif"
    )
    print("=" * 90)

    # Tentukan file database
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_paths = [
        os.path.join(script_dir, "state.vscdb"),
        os.path.join(script_dir, "state(2).vscdb"),
    ]

    db_path = None

    # Cek command line arguments
    if len(sys.argv) > 1:
        provided_path = sys.argv[1]
        if os.path.exists(provided_path):
            db_path = provided_path
        else:
            print(f"❌ [ERROR] File database tidak ditemukan: {provided_path}")
            return

    # Jika tidak ada path di command line, cari di direktori lokal
    if not db_path:
        for path in local_paths:
            if os.path.exists(path):
                db_path = path
                break

    if not db_path:
        print("❌ [ERROR] File state.vscdb tidak ditemukan!")
        print("💡 [SOLUTION] Copy file state.vscdb ke direktori script ini")
        print(
            "📍 [USAGE] python comprehensive_dictionary_analyzer.py [path_to_state.vscdb]"
        )
        return

    print(f"🗃️  [DATABASE] Menggunakan file: {db_path}")

    # Konfirmasi untuk file besar
    file_size = os.path.getsize(db_path)
    if file_size > 100 * 1024 * 1024:  # > 100MB
        print(f"\n⚠️  [WARNING] File berukuran besar ({file_size / 1024 / 1024:.1f} MB)")
        print("Analisis ini akan memproses semua teks dan membuat banyak file.")
        confirm = input("Lanjutkan analisis lengkap? (y/n): ").lower()
        if confirm not in ["y", "yes"]:
            print("❌ [CANCELLED] Analisis dibatalkan")
            return

    # Inisialisasi analyzer
    analyzer = ComprehensiveDictionaryAnalyzer(db_path)

    # Jalankan analisis
    analyzer.run_comprehensive_analysis()


if __name__ == "__main__":
    main()
