#!/usr/bin/env python3
"""
Script optimized untuk menganalisa kata kunci dengan hasil maksimal tapi performa tinggi
Menggunakan batching, optimasi query, dan progress yang lebih baik
Author: AI Assistant
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import re
import time


class OptimizedKeywordAnalyzer:
    def __init__(self, db_path, batch_size=500):
        self.db_path = db_path
        self.conn = None
        self.batch_size = batch_size
        self.results = {
            "keywords": {},
            "summary": {},
            "raw_data": [],
            "total_processed": 0,
        }

        # Daftar kata kunci prioritas (dioptimasi)
        self.target_keywords = {
            "authentication": {
                "keywords": [
                    "token",
                    "auth",
                    "credential",
                    "password",
                    "session",
                    "login",
                ],
                "priority": ["token", "credential", "auth"],  # Kata kunci prioritas
            },
            "subscription": {
                "keywords": [
                    "pro",
                    "plan",
                    "subscription",
                    "trial",
                    "premium",
                    "billing",
                ],
                "priority": ["pro", "plan", "subscription"],
            },
            "ai_features": {
                "keywords": ["ai", "model", "chat", "composer", "copilot", "max mode"],
                "priority": ["ai", "model", "chat"],
            },
            "account_status": {
                "keywords": ["status", "active", "enabled", "disabled"],
                "priority": ["status", "active"],
            },
            "blackbox_specific": {
                "keywords": ["blackbox", "blackboxai", "blackboxapp"],
                "priority": ["blackbox", "blackboxai"],
            },
            "usage_limits": {
                "keywords": ["limit", "quota", "usage", "remaining"],
                "priority": ["limit", "usage"],
            },
        }

        # Cache untuk menghindari query berulang
        self.query_cache = {}

    def connect(self):
        """Koneksi ke database SQLite dengan optimasi"""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ [ERROR] File tidak ditemukan: {self.db_path}")
                return False

            # Optimasi koneksi SQLite
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA journal_mode = WAL")  # Optimasi performa
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA cache_size = 10000")
            self.conn.execute("PRAGMA temp_store = memory")

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

    def search_keywords_optimized(self):
        """Cari kata kunci dengan optimasi performa"""
        print("\n🚀 [OPTIMIZED SEARCH] Memulai pencarian kata kunci optimized...")

        start_time = time.time()
        tables = self.get_tables()
        print(f"📋 [INFO] Menganalisa {len(tables)} tabel: {', '.join(tables)}")

        # Inisialisasi hasil
        for category in self.target_keywords:
            self.results["keywords"][category] = []

        total_matches = 0

        for table_name in tables:
            print(f"\n🔍 [TABLE] Menganalisa tabel: {table_name}")
            table_start = time.time()

            # Gunakan query yang dioptimasi untuk setiap tabel
            table_matches = self._search_table_optimized(table_name)
            table_total = sum(len(matches) for matches in table_matches.values())
            total_matches += table_total

            if table_total > 0:
                # Gabungkan hasil
                for category, matches in table_matches.items():
                    self.results["keywords"][category].extend(matches)
                    self.results["raw_data"].extend(matches)

                table_time = time.time() - table_start
                print(
                    f"   ✅ Ditemukan {table_total} hasil dalam {table_time:.1f} detik"
                )
            else:
                print(f"   ❌ Tidak ada hasil")

        self.results["total_processed"] = total_matches
        elapsed_time = time.time() - start_time

        print(
            f"\n📊 [SUMMARY] Total ditemukan: {total_matches} referensi dalam {elapsed_time:.1f} detik"
        )

        # Summary per kategori
        for category, matches in self.results["keywords"].items():
            if matches:
                print(
                    f"   📁 {category.title().replace('_', ' ')}: {len(matches)} item"
                )

    def _search_table_optimized(self, table_name):
        """Pencarian optimized per tabel"""
        cursor = self.conn.cursor()
        category_matches = {category: [] for category in self.target_keywords}

        try:
            # Dapatkan info kolom (cached)
            cache_key = f"columns_{table_name}"
            if cache_key in self.query_cache:
                columns = self.query_cache[cache_key]
            else:
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = [col[1] for col in cursor.fetchall()]
                self.query_cache[cache_key] = columns

            # Gunakan UNION untuk menggabungkan queries dan mengurangi I/O
            all_conditions = []

            for category, config in self.target_keywords.items():
                # Fokus pada kata kunci prioritas dulu
                priority_keywords = config.get("priority", config["keywords"][:3])

                for keyword in priority_keywords:
                    for col in columns:
                        condition = f"LOWER({col}) LIKE '%{keyword.lower()}%'"
                        all_conditions.append(
                            f"({condition}) as match_{category}_{keyword.replace(' ', '_')}"
                        )

            # Query optimized dengan batching
            base_query = (
                f"SELECT *, " + ", ".join(all_conditions) + f" FROM {table_name}"
            )

            # Eksekusi dengan batching untuk menghindari memory issues
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_rows = cursor.fetchone()[0]

            processed = 0
            batch_num = 0

            while processed < total_rows:
                offset = processed
                batch_query = f"{base_query} LIMIT {self.batch_size} OFFSET {offset}"

                cursor.execute(batch_query)
                batch_rows = cursor.fetchall()

                if not batch_rows:
                    break

                # Proses batch
                self._process_batch(batch_rows, columns, category_matches, table_name)

                processed += len(batch_rows)
                batch_num += 1

                # Progress indicator
                progress = (processed / total_rows) * 100
                print(
                    f"   📊 Batch {batch_num}: {processed}/{total_rows} ({progress:.1f}%)"
                )

        except Exception as e:
            print(f"   ⚠️ Error dalam tabel {table_name}: {e}")

        return category_matches

    def _process_batch(self, rows, columns, category_matches, table_name):
        """Proses batch data untuk efisiensi"""
        for row in rows:
            # Ambil data utama (tanpa kolom match indicator)
            main_data = row[: len(columns)]

            # Tentukan kategori yang cocok berdasarkan isi data
            for category, config in self.target_keywords.items():
                matched_keywords = []

                # Cek apakah ada kata kunci yang cocok
                for col, value in zip(columns, main_data):
                    if value:
                        value_str = str(value).lower()
                        for keyword in config["keywords"]:
                            if keyword.lower() in value_str:
                                if keyword not in matched_keywords:
                                    matched_keywords.append(keyword)

                # Jika ada match, buat data entry
                if matched_keywords:
                    match_data = {
                        "table": table_name,
                        "category": category,
                        "columns": columns,
                        "data": {col: val for col, val in zip(columns, main_data)},
                        "matched_keywords": matched_keywords,
                        "sensitivity": self._determine_sensitivity_fast(
                            matched_keywords, main_data
                        ),
                    }

                    category_matches[category].append(match_data)

    def _determine_sensitivity_fast(self, matched_keywords, data_row):
        """Penentuan sensitivitas yang lebih cepat"""
        high_sensitive_keywords = [
            "token",
            "password",
            "key",
            "secret",
            "credential",
            "auth",
        ]

        # Cek kata kunci yang cocok
        for keyword in matched_keywords:
            if any(
                sensitive in keyword.lower() for sensitive in high_sensitive_keywords
            ):
                return "high"

        # Cek isi data secara cepat
        data_str = " ".join(str(item) for item in data_row if item)[
            :500
        ].lower()  # Limit untuk performa

        if any(sensitive in data_str for sensitive in high_sensitive_keywords):
            return "high"
        elif any(keyword in data_str for keyword in ["userid", "email", "api"]):
            return "medium"

        return "low"

    def extract_key_credentials(self):
        """Extract kredensial penting dengan optimasi"""
        print("\n🔑 [KEY CREDENTIALS] Mengekstrak kredensial penting...")

        key_findings = {
            "blackbox_credentials": [],
            "cursor_tokens": [],
            "subscription_info": [],
            "user_identifiers": [],
            "api_configurations": [],
        }

        # Proses data yang sudah dikategorikan
        for category, matches in self.results["keywords"].items():
            if category == "blackbox_specific":
                for match in matches:
                    if "blackbox" in str(match.get("matched_keywords", [])).lower():
                        key_findings["blackbox_credentials"].append(
                            self._extract_key_info(match)
                        )

            elif category == "authentication":
                for match in matches:
                    if any(
                        keyword in str(match.get("matched_keywords", [])).lower()
                        for keyword in ["token", "credential"]
                    ):
                        key_findings["cursor_tokens"].append(
                            self._extract_key_info(match)
                        )

            elif category == "subscription":
                for match in matches:
                    if any(
                        keyword in str(match.get("matched_keywords", [])).lower()
                        for keyword in ["pro", "plan", "trial"]
                    ):
                        key_findings["subscription_info"].append(
                            self._extract_key_info(match)
                        )

        # Tampilkan hasil
        for finding_type, items in key_findings.items():
            if items:
                print(
                    f"   🎯 {finding_type.title().replace('_', ' ')}: {len(items)} items"
                )

        return key_findings

    def _extract_key_info(self, match):
        """Extract informasi kunci dari match"""
        key_info = {
            "table": match["table"],
            "keywords": match["matched_keywords"],
            "sensitivity": match["sensitivity"],
            "summary": {},
        }

        # Extract info penting dari data
        for col, value in match["data"].items():
            if value:
                # Cek untuk info kredensial
                col_lower = col.lower()
                if any(
                    keyword in col_lower
                    for keyword in ["user", "id", "token", "key", "plan"]
                ):
                    if isinstance(value, str) and len(value) > 50:
                        # Preview untuk data panjang
                        key_info["summary"][
                            col
                        ] = f"{value[:30]}...({len(value)} chars)"
                    else:
                        key_info["summary"][col] = value

        return key_info

    def generate_comprehensive_report(self):
        """Generate laporan komprehensif dengan semua data"""
        print("\n" + "=" * 80)
        print("📊 [COMPREHENSIVE REPORT] LAPORAN LENGKAP ANALISIS")
        print("=" * 80)

        total_matches = len(self.results["raw_data"])
        high_sensitive = len(
            [m for m in self.results["raw_data"] if m.get("sensitivity") == "high"]
        )
        medium_sensitive = len(
            [m for m in self.results["raw_data"] if m.get("sensitivity") == "medium"]
        )

        print(f"🗃️  Database: {self.db_path}")
        print(f"📅 Tanggal analisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Total item dianalisis: {total_matches:,}")

        print(f"\n🚨 TINGKAT SENSITIVITAS:")
        high_percentage = (
            (high_sensitive / total_matches * 100) if total_matches > 0 else 0
        )
        medium_percentage = (
            (medium_sensitive / total_matches * 100) if total_matches > 0 else 0
        )
        print(f"   🔴 High Sensitive: {high_sensitive:,} ({high_percentage:.1f}%)")
        print(
            f"   🟡 Medium Sensitive: {medium_sensitive:,} ({medium_percentage:.1f}%)"
        )
        print(
            f"   🟢 Low Sensitive: {total_matches - high_sensitive - medium_sensitive:,}"
        )

        print(f"\n📂 DISTRIBUSI LENGKAP PER KATEGORI:")
        for category, matches in sorted(
            self.results["keywords"].items(), key=lambda x: len(x[1]), reverse=True
        ):
            if matches:
                high_in_cat = len(
                    [m for m in matches if m.get("sensitivity") == "high"]
                )
                percentage = (len(matches) / total_matches) * 100
                print(
                    f"   • {category.title().replace('_', ' ')}: {len(matches):,} ({percentage:.1f}%) | {high_in_cat:,} high sensitive"
                )

        # Top keywords per kategori
        print(f"\n🏆 TOP KEYWORDS PER KATEGORI:")
        for category, matches in self.results["keywords"].items():
            if matches:
                keyword_count = defaultdict(int)
                for match in matches:
                    for keyword in match.get("matched_keywords", []):
                        keyword_count[keyword] += 1

                top_keywords = sorted(
                    keyword_count.items(), key=lambda x: x[1], reverse=True
                )[:5]
                print(f"   📁 {category.title().replace('_', ' ')}:")
                for keyword, count in top_keywords:
                    print(f"      - {keyword}: {count:,} occurrences")

    def export_comprehensive_results(self, output_file=None, include_sensitive=False):
        """Export hasil lengkap dengan struktur yang optimal"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"comprehensive_keyword_analysis_{timestamp}.json"

        # Struktur export yang optimized
        export_data = {
            "analysis_info": {
                "database_file": self.db_path,
                "analysis_date": datetime.now().isoformat(),
                "total_matches": len(self.results["raw_data"]),
                "batch_size_used": self.batch_size,
                "include_sensitive_data": include_sensitive,
            },
            "summary": {
                "categories": {
                    cat: len(matches)
                    for cat, matches in self.results["keywords"].items()
                },
                "sensitivity_distribution": {
                    "high": len(
                        [
                            m
                            for m in self.results["raw_data"]
                            if m.get("sensitivity") == "high"
                        ]
                    ),
                    "medium": len(
                        [
                            m
                            for m in self.results["raw_data"]
                            if m.get("sensitivity") == "medium"
                        ]
                    ),
                    "low": len(
                        [
                            m
                            for m in self.results["raw_data"]
                            if m.get("sensitivity") == "low"
                        ]
                    ),
                },
            },
            "detailed_results": {},
        }

        # Export results dengan batching untuk file besar
        print(f"\n💾 [EXPORT] Mengexport {len(self.results['raw_data']):,} items...")

        for category, matches in self.results["keywords"].items():
            if matches:
                print(f"   📁 Exporting {category}: {len(matches):,} items...")

                category_data = []
                for i, match in enumerate(matches):
                    # Progress untuk kategori besar
                    if i % 1000 == 0 and i > 0:
                        print(f"      📊 Progress: {i:,}/{len(matches):,}")

                    # Filter data sensitif jika diperlukan
                    if not include_sensitive and match.get("sensitivity") == "high":
                        match_data = {
                            "table": match["table"],
                            "category": match["category"],
                            "matched_keywords": match["matched_keywords"],
                            "sensitivity": match["sensitivity"],
                            "data_summary": f"[FILTERED - {len(match['data'])} sensitive fields]",
                        }
                    else:
                        match_data = {
                            "table": match["table"],
                            "category": match["category"],
                            "matched_keywords": match["matched_keywords"],
                            "sensitivity": match["sensitivity"],
                            "data": {},
                        }

                        # Process data dengan JSON parsing
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

        # Simpan dengan kompresi untuk file besar
        try:
            print(f"   💽 Writing to file: {output_file}")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)

            file_size = os.path.getsize(output_file)
            print(f"\n✅ [SUCCESS] Export berhasil!")
            print(f"📄 File: {output_file}")
            print(f"📊 Size: {file_size:,} bytes ({file_size / 1024 / 1024:.1f} MB)")

            if not include_sensitive:
                print("⚠️  [NOTICE] Data highly sensitive telah disensor")

            return output_file
        except Exception as e:
            print(f"❌ [ERROR] Gagal export: {e}")
            return None


def main():
    print("🚀 [OPTIMIZED KEYWORD ANALYZER] Analisis Maksimal dengan Performa Tinggi")
    print("=" * 80)
    print("🎯 Target: SEMUA data token, kredensial, subscription, AI features, dll")
    print("⚡ Optimasi: Batching, caching, progress tracking")
    print("=" * 80)

    # Setup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_paths = [
        os.path.join(script_dir, "state.vscdb"),
        os.path.join(script_dir, "state(2).vscdb"),
    ]

    db_path = None
    batch_size = 500

    # Parse arguments
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith("--batch-size="):
                batch_size = int(arg.split("=")[1])
            elif os.path.exists(arg):
                db_path = arg
            elif not db_path:
                print(f"❌ [ERROR] File tidak ditemukan: {arg}")
                return

    if not db_path:
        for path in local_paths:
            if os.path.exists(path):
                db_path = path
                break

    if not db_path:
        print("❌ [ERROR] File state.vscdb tidak ditemukan!")
        print("💡 [SOLUTION] Copy file state.vscdb ke direktori script ini")
        print(
            "📍 [USAGE] python keyword_analyzer_optimized.py [path] [--batch-size=500]"
        )
        return

    print(f"🗃️  [DATABASE] File: {db_path}")
    print(f"⚙️  [CONFIG] Batch size: {batch_size}")

    # Konfirmasi untuk file besar
    file_size = os.path.getsize(db_path)
    if file_size > 100 * 1024 * 1024:  # > 100MB
        print(f"\n⚠️  [WARNING] File berukuran besar ({file_size / 1024 / 1024:.1f} MB)")
        confirm = input("Lanjutkan analisis lengkap? (y/n): ").lower()
        if confirm not in ["y", "yes"]:
            print("❌ [CANCELLED] Analisis dibatalkan")
            return

    # Inisialisasi analyzer
    analyzer = OptimizedKeywordAnalyzer(db_path, batch_size=batch_size)

    try:
        start_time = time.time()

        # Koneksi
        if not analyzer.connect():
            return

        print("\n🚀 [START] Memulai analisis optimized...")

        # 1. Pencarian kata kunci optimized
        analyzer.search_keywords_optimized()

        if len(analyzer.results["raw_data"]) == 0:
            print("\n❌ [RESULT] Tidak ada kata kunci ditemukan")
            return

        # 2. Extract kredensial penting
        key_credentials = analyzer.extract_key_credentials()

        # 3. Generate laporan komprehensif
        analyzer.generate_comprehensive_report()

        # 4. Export
        print("\n💾 [EXPORT OPTIONS]")
        print("1. Export lengkap tanpa sensor (SEMUA data)")
        print("2. Export dengan sensor data sensitif")
        print("3. Tidak export")

        choice = input("Pilih opsi (1/2/3): ").strip()

        if choice == "1":
            confirm = input(
                "⚠️  Export SEMUA data termasuk sensitif? (yes/no): "
            ).lower()
            if confirm in ["yes", "y"]:
                export_file = analyzer.export_comprehensive_results(
                    include_sensitive=True
                )
            else:
                export_file = analyzer.export_comprehensive_results(
                    include_sensitive=False
                )
        elif choice == "2":
            export_file = analyzer.export_comprehensive_results(include_sensitive=False)

        total_time = time.time() - start_time

        print(f"\n🎉 [COMPLETED] Analisis lengkap selesai!")
        print(f"⏱️  Total waktu: {total_time:.1f} detik")
        print(f"📊 Total diproses: {len(analyzer.results['raw_data']):,} items")

        if "export_file" in locals() and export_file:
            print(f"📄 Export file: {export_file}")

    except Exception as e:
        print(f"❌ [ERROR] Terjadi kesalahan: {e}")
        import traceback

        traceback.print_exc()

    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
