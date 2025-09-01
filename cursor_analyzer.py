#!/usr/bin/env python3
"""
Script khusus untuk menganalisa kata kunci "cursor" di file state.vscdb
Dibuat untuk mengidentifikasi semua referensi "cursor" dan konteks penggunaannya
Author: AI Assistant
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import re


class CursorAnalyzer:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.results = {
            "total_matches": 0,
            "categories": defaultdict(list),
            "raw_data": [],
        }

        # Kategori untuk mengklasifikasi hasil
        self.categories = {
            "settings": ["setting", "config", "preference", "option"],
            "ui": ["workbench", "view", "panel", "sidebar", "explorer"],
            "editor": ["editor", "text", "file", "document"],
            "extension": ["extension", "plugin", "addon"],
            "history": ["history", "recent", "opened", "path"],
            "theme": ["theme", "color", "appearance"],
            "key_binding": ["keybinding", "shortcut", "key"],
            "window": ["window", "layout", "position"],
            "debug": ["debug", "debugger", "breakpoint"],
            "git": ["git", "scm", "source"],
            "search": ["search", "find", "replace"],
            "terminal": ["terminal", "shell", "command"],
            "other": [],
        }

    def connect(self):
        """Koneksi ke database SQLite"""
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
        """Tutup koneksi database"""
        if self.conn:
            self.conn.close()

    def get_tables(self):
        """Dapatkan daftar semua tabel dalam database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in cursor.fetchall()]

    def search_cursor_references(self):
        """Cari semua referensi kata 'cursor' dalam database"""
        print("\n🔍 [SEARCH] Mencari referensi kata 'cursor'...")

        tables = self.get_tables()
        print(f"📋 [INFO] Mencari di {len(tables)} tabel: {', '.join(tables)}")

        total_matches = 0

        for table_name in tables:
            print(f"\n🔍 [TABLE] Menganalisa tabel: {table_name}")
            matches = self._search_in_table(table_name)
            total_matches += len(matches)

            if matches:
                print(f"   ✅ Ditemukan {len(matches)} hasil")
                self.results["raw_data"].extend(matches)
            else:
                print(f"   ❌ Tidak ada hasil")

        self.results["total_matches"] = total_matches
        print(f"\n📊 [SUMMARY] Total ditemukan: {total_matches} referensi 'cursor'")

    def _search_in_table(self, table_name):
        """Cari kata 'cursor' dalam tabel tertentu"""
        cursor = self.conn.cursor()
        matches = []

        try:
            # Dapatkan info kolom
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            # Buat query pencarian
            search_conditions = []
            for col in columns:
                search_conditions.append(f"LOWER({col}) LIKE '%cursor%'")

            query = f"SELECT * FROM {table_name} WHERE {' OR '.join(search_conditions)}"
            cursor.execute(query)
            rows = cursor.fetchall()

            # Proses hasil
            for row in rows:
                match_data = {"table": table_name, "columns": columns, "data": {}}

                for col, value in zip(columns, row):
                    match_data["data"][col] = value

                matches.append(match_data)

        except Exception as e:
            print(f"   ⚠️ Error dalam tabel {table_name}: {e}")

        return matches

    def categorize_results(self):
        """Kategorikan hasil berdasarkan konteks"""
        print("\n📂 [CATEGORIZE] Mengkategorikan hasil...")

        for match in self.results["raw_data"]:
            categorized = False

            # Gabungkan semua data untuk analisis
            all_text = ""
            for col, value in match["data"].items():
                if value:
                    all_text += f" {col} {str(value)}"

            all_text = all_text.lower()

            # Cari kategori yang sesuai
            for category, keywords in self.categories.items():
                if category == "other":
                    continue

                for keyword in keywords:
                    if keyword in all_text:
                        self.results["categories"][category].append(match)
                        categorized = True
                        break

                if categorized:
                    break

            # Jika tidak masuk kategori manapun, masukkan ke 'other'
            if not categorized:
                self.results["categories"]["other"].append(match)

        # Tampilkan summary kategorisasi
        for category, matches in self.results["categories"].items():
            if matches:
                print(f"   📁 {category.title()}: {len(matches)} item")

    def analyze_cursor_contexts(self):
        """Analisis konteks penggunaan kata 'cursor'"""
        print("\n🔬 [ANALYSIS] Menganalisis konteks penggunaan 'cursor'...")

        context_patterns = {
            "Cursor App/Editor": [
                r"cursor.*editor",
                r"cursor.*app",
                r"cursor.*ide",
                r"editor.*cursor",
                r"app.*cursor",
            ],
            "Cursor Position": [
                r"cursor.*position",
                r"cursor.*line",
                r"cursor.*column",
                r"position.*cursor",
                r"line.*cursor",
            ],
            "Cursor Style/Appearance": [
                r"cursor.*style",
                r"cursor.*color",
                r"cursor.*theme",
                r"cursor.*appearance",
                r"cursor.*blink",
            ],
            "Cursor Movement": [
                r"cursor.*move",
                r"cursor.*jump",
                r"cursor.*navigate",
                r"move.*cursor",
                r"jump.*cursor",
            ],
            "Cursor Settings": [
                r"cursor.*setting",
                r"cursor.*config",
                r"cursor.*preference",
                r"setting.*cursor",
                r"config.*cursor",
            ],
        }

        context_results = defaultdict(list)

        for match in self.results["raw_data"]:
            # Gabungkan semua data untuk analisis
            all_text = ""
            for col, value in match["data"].items():
                if value:
                    all_text += f" {str(value)}"

            all_text = all_text.lower()

            # Cari pattern yang cocok
            matched_context = False
            for context, patterns in context_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, all_text):
                        context_results[context].append(match)
                        matched_context = True
                        break
                if matched_context:
                    break

            if not matched_context:
                context_results["Lainnya"].append(match)

        # Tampilkan hasil analisis konteks
        print("\n📊 [CONTEXT ANALYSIS] Hasil analisis konteks:")
        for context, matches in context_results.items():
            print(f"   🏷️  {context}: {len(matches)} item")

        return context_results

    def display_detailed_results(self, max_items_per_category=5):
        """Tampilkan hasil detail dengan format yang mudah dibaca"""
        print("\n" + "=" * 80)
        print("📋 [DETAILED RESULTS] HASIL DETAIL ANALISIS 'CURSOR'")
        print("=" * 80)

        for category, matches in self.results["categories"].items():
            if not matches:
                continue

            print(f"\n📂 [KATEGORI] {category.upper()}")
            print("-" * 60)
            print(f"Total item: {len(matches)}")

            # Tampilkan beberapa item pertama
            for i, match in enumerate(matches[:max_items_per_category], 1):
                print(f"\n   📄 [ITEM {i}] Table: {match['table']}")

                for col, value in match["data"].items():
                    if value and "cursor" in str(value).lower():
                        formatted_value = self._format_value(value)
                        print(f"      🔑 {col}:")

                        # Highlight kata 'cursor'
                        if "cursor" in str(value).lower():
                            print(f"         {formatted_value}")
                        else:
                            print(f"         {formatted_value}")

            if len(matches) > max_items_per_category:
                print(
                    f"   ⚠️  ... dan {len(matches) - max_items_per_category} item lainnya"
                )

    def _format_value(self, value, max_length=200):
        """Format nilai untuk ditampilkan dengan lebih rapi"""
        if value is None:
            return "NULL"

        value_str = str(value)

        # Coba parse sebagai JSON
        try:
            if value_str.strip().startswith(("{", "[")):
                parsed = json.loads(value_str)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)

                # Highlight kata 'cursor' dalam JSON
                lines = formatted.split("\n")
                highlighted_lines = []
                for line in lines:
                    if "cursor" in line.lower():
                        highlighted_lines.append(f"         >>> {line}")
                    else:
                        highlighted_lines.append(f"             {line}")

                result = "\n".join(highlighted_lines)
                if len(result) > max_length * 3:
                    return result[: max_length * 3] + "\n         ... [JSON DIPOTONG]"
                return result
        except:
            pass

        # Untuk string biasa
        if len(value_str) > max_length:
            return value_str[:max_length] + " ... [DIPOTONG]"

        # Highlight kata 'cursor'
        if "cursor" in value_str.lower():
            return f">>> {value_str}"

        return value_str

    def export_results(self, output_file=None):
        """Export hasil ke file JSON"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"cursor_analysis_{timestamp}.json"

        export_data = {
            "analysis_info": {
                "database_file": self.db_path,
                "analysis_date": datetime.now().isoformat(),
                "total_matches": self.results["total_matches"],
            },
            "summary": {
                "categories": {
                    cat: len(matches)
                    for cat, matches in self.results["categories"].items()
                }
            },
            "detailed_results": {},
        }

        # Export detailed results
        for category, matches in self.results["categories"].items():
            if matches:
                category_data = []
                for match in matches:
                    # Konversi data untuk JSON serialization
                    match_data = {"table": match["table"], "data": {}}

                    for col, value in match["data"].items():
                        if isinstance(value, str) and value.strip().startswith(
                            ("{", "[")
                        ):
                            try:
                                match_data["data"][col] = json.loads(value)
                            except:
                                match_data["data"][col] = value
                        else:
                            match_data["data"][col] = value

                    category_data.append(match_data)

                export_data["detailed_results"][category] = category_data

        try:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n💾 [EXPORT] Hasil berhasil diexport ke: {output_file}")
            return output_file
        except Exception as e:
            print(f"❌ [ERROR] Gagal export: {e}")
            return None

    def generate_summary_report(self):
        """Generate laporan ringkasan analisis"""
        print("\n" + "=" * 80)
        print("📊 [SUMMARY REPORT] LAPORAN RINGKASAN ANALISIS")
        print("=" * 80)

        print(f"🗃️  Database: {self.db_path}")
        print(f"📅 Tanggal analisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Total referensi 'cursor': {self.results['total_matches']}")

        print(f"\n📂 Distribusi per kategori:")
        for category, matches in sorted(
            self.results["categories"].items(), key=lambda x: len(x[1]), reverse=True
        ):
            if matches:
                percentage = (len(matches) / self.results["total_matches"]) * 100
                print(f"   • {category.title()}: {len(matches)} ({percentage:.1f}%)")

        # Identifikasi kategori terbanyak
        if self.results["categories"]:
            max_category = max(
                self.results["categories"].items(), key=lambda x: len(x[1])
            )
            print(
                f"\n🏆 Kategori terbanyak: {max_category[0].title()} ({len(max_category[1])} item)"
            )

        # Rekomendasi
        print(f"\n💡 [REKOMENDASI]")
        if self.results["total_matches"] > 50:
            print(
                "   • Dataset cukup besar, pertimbangkan analisis lebih detail per kategori"
            )
        if len(self.results["categories"]["other"]) > len(
            self.results["categories"].get("settings", [])
        ):
            print(
                "   • Banyak item tidak terkategorisasi, mungkin perlu kategori tambahan"
            )

        print("=" * 80)


def main():
    print("🎯 [CURSOR ANALYZER] Script Analisis Kata Kunci 'Cursor'")
    print("=" * 60)

    # Tentukan file database
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_paths = [
        os.path.join(script_dir, "state.vscdb"),
        os.path.join(script_dir, "state(2).vscdb"),
    ]

    db_path = None
    if len(sys.argv) > 1:
        provided_path = sys.argv[1]
        if os.path.exists(provided_path):
            db_path = provided_path
        else:
            print(f"❌ [ERROR] File tidak ditemukan: {provided_path}")
            return
    else:
        for path in local_paths:
            if os.path.exists(path):
                db_path = path
                break

    if not db_path:
        print("❌ [ERROR] File state.vscdb tidak ditemukan!")
        print("💡 [SOLUTION] Copy file state.vscdb ke direktori script ini")
        print("📍 [USAGE] python cursor_analyzer.py [path_to_state.vscdb]")
        return

    print(f"🗃️  [DATABASE] Menggunakan file: {db_path}")

    # Inisialisasi analyzer
    analyzer = CursorAnalyzer(db_path)

    try:
        # Koneksi ke database
        if not analyzer.connect():
            return

        # Mulai analisis
        print("\n🚀 [START] Memulai analisis kata kunci 'cursor'...")

        # 1. Cari semua referensi
        analyzer.search_cursor_references()

        if analyzer.results["total_matches"] == 0:
            print("\n❌ [RESULT] Tidak ada referensi 'cursor' ditemukan")
            return

        # 2. Kategorikan hasil
        analyzer.categorize_results()

        # 3. Analisis konteks
        context_results = analyzer.analyze_cursor_contexts()

        # 4. Tampilkan hasil detail
        analyzer.display_detailed_results()

        # 5. Generate summary report
        analyzer.generate_summary_report()

        # 6. Export hasil
        export_choice = input("\n💾 Apakah ingin export hasil ke JSON? (y/n): ").lower()
        if export_choice in ["y", "yes"]:
            export_file = analyzer.export_results()
            if export_file:
                print(f"✅ [SUCCESS] Analisis selesai dan diexport ke: {export_file}")

        print("\n🎉 [COMPLETED] Analisis selesai!")

    except Exception as e:
        print(f"❌ [ERROR] Terjadi kesalahan: {e}")

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()


