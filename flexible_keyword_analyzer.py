#!/usr/bin/env python3
"""
Script Fleksibel untuk Menganalisis Kata Kunci Bebas di Database state.vscdb
Dibuat untuk menerima input kata kunci apapun dan mencari di seluruh database
Author: AI Assistant
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import re


class FlexibleKeywordAnalyzer:
    def __init__(self, db_path, keywords, output_file=None, max_results=1000):
        self.db_path = db_path
        self.keywords = keywords if isinstance(keywords, list) else [keywords]
        self.output_file = output_file
        self.max_results = max_results
        self.conn = None
        self.results = {
            "keywords_searched": self.keywords,
            "total_matches": 0,
            "tables_analyzed": [],
            "matches_by_table": {},
            "detailed_matches": [],
            "analysis_timestamp": datetime.now().isoformat(),
        }

    def connect(self):
        """Membuat koneksi ke database SQLite"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ [ERROR] File tidak ditemukan: {self.db_path}")
                return False

            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ [SUCCESS] Berhasil terhubung ke database: {self.db_path}")

            # Info file
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

    def search_keywords(self):
        """Mencari kata kunci di seluruh database"""
        print(
            f"\n🔍 [SEARCH] Mencari {len(self.keywords)} kata kunci: {', '.join(self.keywords)}"
        )

        tables = self.get_tables()
        print(f"📋 [INFO] Menganalisa {len(tables)} tabel: {', '.join(tables)}")

        total_matches = 0

        for table_name in tables:
            print(f"\n🔍 [TABLE] Menganalisa tabel: {table_name}")
            table_matches = self._search_in_table(table_name)

            if table_matches:
                self.results["matches_by_table"][table_name] = len(table_matches)
                self.results["detailed_matches"].extend(table_matches)
                total_matches += len(table_matches)
                print(f"   ✅ Ditemukan {len(table_matches)} hasil")
            else:
                print(f"   ❌ Tidak ada hasil")

            # Cek batas maksimal hasil
            if total_matches >= self.max_results:
                print(f"⚠️  [WARNING] Mencapai batas maksimal {self.max_results} hasil")
                break

        self.results["total_matches"] = total_matches
        self.results["tables_analyzed"] = tables

        print(
            f"\n📊 [SUMMARY] Total ditemukan: {total_matches} hasil untuk kata kunci yang dicari"
        )

        if total_matches == 0:
            print(
                "💡 [INFO] Tidak ada hasil ditemukan. Coba kata kunci lain atau periksa ejaan."
            )

    def _search_in_table(self, table_name):
        """Mencari kata kunci dalam tabel tertentu"""
        cursor = self.conn.cursor()
        matches = []

        try:
            # Dapatkan info kolom
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            # Buat kondisi pencarian untuk setiap kata kunci
            search_conditions = []
            for keyword in self.keywords:
                for col in columns:
                    # Gunakan LIKE untuk pencarian case-insensitive
                    search_conditions.append(f"LOWER({col}) LIKE '%{keyword.lower()}%'")

            if search_conditions:
                query = (
                    f"SELECT * FROM {table_name} WHERE {' OR '.join(search_conditions)}"
                )
                cursor.execute(query)
                rows = cursor.fetchall()

                # Proses hasil
                for row in rows:
                    match_data = {
                        "table": table_name,
                        "columns": columns,
                        "data": {},
                        "matched_keywords": [],
                        "match_timestamp": datetime.now().isoformat(),
                    }

                    # Simpan data dan identifikasi kata kunci yang cocok
                    for col, value in zip(columns, row):
                        match_data["data"][col] = value

                        # Cek kata kunci yang cocok
                        if value:
                            value_str = str(value).lower()
                            for keyword in self.keywords:
                                if keyword.lower() in value_str:
                                    if keyword not in match_data["matched_keywords"]:
                                        match_data["matched_keywords"].append(keyword)

                    matches.append(match_data)

                    # Cek batas maksimal per tabel
                    if len(matches) >= self.max_results:
                        break

        except Exception as e:
            print(f"   ⚠️ Error dalam tabel {table_name}: {e}")

        return matches

    def display_results(self):
        """Menampilkan hasil pencarian di konsol"""
        print("\n" + "=" * 80)
        print("📋 [HASIL PENCARIAN] DETAIL HASIL ANALISIS KATA KUNCI")
        print("=" * 80)

        print(f"🔍 Kata kunci yang dicari: {', '.join(self.keywords)}")
        print(f"📊 Total hasil: {self.results['total_matches']}")
        print(f"📋 Tabel yang dianalisa: {len(self.results['tables_analyzed'])}")

        if self.results["total_matches"] == 0:
            print("\n❌ Tidak ada hasil ditemukan.")
            return

        # Tampilkan distribusi per tabel
        print(f"\n📂 Distribusi hasil per tabel:")
        for table, count in self.results["matches_by_table"].items():
            print(f"   • {table}: {count} hasil")

        # Tampilkan beberapa hasil pertama
        print(f"\n📄 [HASIL DETAIL] (menampilkan maksimal 5 hasil pertama per tabel):")
        table_display_count = defaultdict(int)

        for match in self.results["detailed_matches"]:
            table = match["table"]
            if table_display_count[table] >= 5:
                continue

            print(f"\n   📋 Tabel: {table}")
            print(
                f"      🏷️  Kata kunci yang cocok: {', '.join(match['matched_keywords'])}"
            )

            for col, value in match["data"].items():
                if value and any(
                    keyword.lower() in str(value).lower()
                    for keyword in match["matched_keywords"]
                ):
                    formatted_value = self._format_value(value)
                    print(f"      🔑 {col}:")
                    print(f"         {formatted_value}")

            table_display_count[table] += 1

        if self.results["total_matches"] > sum(table_display_count.values()):
            remaining = self.results["total_matches"] - sum(
                table_display_count.values()
            )
            print(f"\n   ⚠️  ... dan {remaining} hasil lainnya")

    def _format_value(self, value, max_length=200):
        """Format nilai untuk ditampilkan dengan rapi"""
        if value is None:
            return "NULL"

        value_str = str(value)

        # Coba parse sebagai JSON
        try:
            if value_str.strip().startswith(("{", "[")):
                parsed = json.loads(value_str)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)

                if len(formatted) > max_length * 3:
                    return (
                        formatted[: max_length * 3] + "\n         ... [JSON DIPOTONG]"
                    )
                return formatted
        except:
            pass

        # Untuk string biasa
        if len(value_str) > max_length:
            return value_str[:max_length] + " ... [DIPOTONG]"

        return value_str

    def export_results(self):
        """Export hasil ke file JSON"""
        if not self.output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = f"keyword_search_{timestamp}.json"

        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n💾 [EXPORT] Hasil berhasil disimpan ke: {self.output_file}")
            print(f"📊 Total hasil yang diexport: {self.results['total_matches']}")
            return self.output_file
        except Exception as e:
            print(f"❌ [ERROR] Gagal export: {e}")
            return None


def get_keywords_from_input():
    """Mendapatkan kata kunci dari input pengguna"""
    if len(sys.argv) > 2:
        # Kata kunci dari command line arguments
        return sys.argv[2:]
    else:
        # Input interaktif
        print(
            "🔍 [INPUT] Masukkan kata kunci yang ingin dicari (pisahkan dengan koma):"
        )
        keywords_input = input("Kata kunci: ").strip()

        if not keywords_input:
            print("❌ [ERROR] Kata kunci tidak boleh kosong!")
            return None

        # Split berdasarkan koma dan bersihkan spasi
        keywords = [kw.strip() for kw in keywords_input.split(",") if kw.strip()]

        if not keywords:
            print("❌ [ERROR] Tidak ada kata kunci valid!")
            return None

        return keywords


def main():
    print("🎯 [FLEXIBLE KEYWORD ANALYZER] Script Analisis Kata Kunci Fleksibel")
    print("=" * 70)
    print("🔍 Script ini dapat mencari kata kunci APAPUN di database state.vscdb")
    print("=" * 70)

    # Tentukan file database
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_paths = [
        os.path.join(script_dir, "state.vscdb"),
        os.path.join(script_dir, "state(2).vscdb"),
    ]

    db_path = None

    # Cek command line arguments untuk path database
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
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
            "📍 [USAGE] python flexible_keyword_analyzer.py [path_to_db] [keyword1] [keyword2] ..."
        )
        print(
            "📍 [USAGE] python flexible_keyword_analyzer.py [path_to_db]  # untuk input interaktif"
        )
        return

    print(f"🗃️  [DATABASE] Menggunakan file: {db_path}")

    # Dapatkan kata kunci
    keywords = get_keywords_from_input()
    if not keywords:
        return

    print(f"🔍 [KEYWORDS] Mencari {len(keywords)} kata kunci: {', '.join(keywords)}")

    # Opsi tambahan dari command line
    max_results = 1000
    if "--max-results" in sys.argv:
        try:
            idx = sys.argv.index("--max-results")
            max_results = int(sys.argv[idx + 1])
        except:
            print("⚠️  [WARNING] Invalid --max-results value, using default 1000")

    # Inisialisasi analyzer
    analyzer = FlexibleKeywordAnalyzer(db_path, keywords, max_results=max_results)

    try:
        # Koneksi ke database
        if not analyzer.connect():
            return

        # Lakukan pencarian
        print("\n🚀 [START] Memulai pencarian kata kunci...")
        analyzer.search_keywords()

        # Tampilkan hasil di konsol
        analyzer.display_results()

        # Export ke file JSON
        export_file = analyzer.export_results()

        print("\n🎉 [COMPLETED] Pencarian kata kunci selesai!")

        if export_file:
            print(f"📄 File hasil: {export_file}")

        print(
            "\n💡 [TIPS] Gunakan --max-results <number> untuk membatasi hasil pencarian"
        )
        print("💡 [TIPS] Contoh: python flexible_keyword_analyzer.py --max-results 500")

    except Exception as e:
        print(f"❌ [ERROR] Terjadi kesalahan: {e}")
        import traceback

        traceback.print_exc()

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
