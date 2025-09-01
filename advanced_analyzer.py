#!/usr/bin/env python3
"""
Advanced Script untuk menganalisa berbagai kata kunci penting di file state.vscdb
Output diorganisir dalam struktur folder & file yang mudah dibaca
Author: AI Assistant
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import re
from pathlib import Path


class AdvancedKeywordAnalyzer:
    def __init__(
        self, db_path, output_dir="analysis_output", quick_mode=False, max_items=1000
    ):
        self.db_path = db_path
        self.output_dir = Path(output_dir)
        self.conn = None
        self.quick_mode = quick_mode
        self.max_items = max_items
        self.results = {"keywords": {}, "summary": {}, "raw_data": []}

        # Daftar kata kunci penting untuk dianalisa
        self.target_keywords = {
            "authentication": {
                "keywords": [
                    "token",
                    "auth",
                    "login",
                    "logout",
                    "credential",
                    "password",
                    "session",
                ],
                "patterns": [
                    r"token",
                    r"auth.*token",
                    r"access.*token",
                    r"refresh.*token",
                    r"credential",
                    r"auth.*key",
                    r"api.*key",
                    r"login",
                    r"logout",
                    r"session",
                    r"password",
                    r"bearer",
                ],
            },
            "subscription": {
                "keywords": [
                    "pro",
                    "plan",
                    "subscription",
                    "trial",
                    "premium",
                    "paid",
                    "billing",
                ],
                "patterns": [
                    r"pro.*plan",
                    r"pro.*trial",
                    r"subscription",
                    r"premium",
                    r"billing",
                    r"paid",
                    r"trial.*end",
                    r"plan.*type",
                    r"membership",
                    r"upgrade",
                    r"downgrade",
                ],
            },
            "ai_features": {
                "keywords": ["max mode", "ai", "model", "chat", "composer", "copilot"],
                "patterns": [
                    r"max.*mode",
                    r"ai.*model",
                    r"chat.*model",
                    r"composer",
                    r"copilot",
                    r"code.*generation",
                    r"ai.*feature",
                ],
            },
            "account_status": {
                "keywords": [
                    "status",
                    "active",
                    "inactive",
                    "enabled",
                    "disabled",
                    "banned",
                ],
                "patterns": [
                    r"account.*status",
                    r"user.*status",
                    r"active",
                    r"inactive",
                    r"enabled",
                    r"disabled",
                    r"banned",
                    r"suspended",
                ],
            },
            "blackbox_specific": {
                "keywords": ["blackbox", "blackboxai", "blackboxapp"],
                "patterns": [
                    r"blackbox.*agent",
                    r"blackbox.*auth",
                    r"blackbox.*user",
                    r"blackbox.*api",
                    r"blackbox.*key",
                    r"blackbox.*pro",
                ],
            },
            "usage_limits": {
                "keywords": ["limit", "quota", "usage", "remaining", "consumed"],
                "patterns": [
                    r"usage.*limit",
                    r"quota",
                    r"remaining.*usage",
                    r"consumed",
                    r"rate.*limit",
                    r"api.*limit",
                ],
            },
        }

        # Kategori data sensitif
        self.sensitive_categories = {
            "high_sensitive": ["token", "password", "key", "secret", "credential"],
            "medium_sensitive": ["userid", "email", "api", "auth"],
            "low_sensitive": ["plan", "status", "mode", "feature"],
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

    def create_output_structure(self):
        """Buat struktur folder output"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"analysis_output_{timestamp}")
        self.output_dir.mkdir(exist_ok=True)

        # Buat subfolder untuk setiap kategori
        for category in self.target_keywords.keys():
            (self.output_dir / category).mkdir(exist_ok=True)

        # Buat folder untuk summary dan reports
        (self.output_dir / "summary").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)
        (self.output_dir / "data").mkdir(exist_ok=True)

        print(f"📁 [OUTPUT] Struktur folder dibuat di: {self.output_dir}")

    def search_keywords(self):
        """Cari semua kata kunci target dalam database"""
        if self.quick_mode:
            print(
                f"\n⚡ [QUICK SEARCH] Mode cepat - maksimal {self.max_items} hasil per kategori"
            )
        else:
            print("\n🔍 [SEARCH] Mencari kata kunci target...")

        tables = self.get_tables()
        print(f"📋 [INFO] Menganalisa {len(tables)} tabel: {', '.join(tables)}")

        # Inisialisasi hasil untuk setiap kategori
        for category in self.target_keywords:
            self.results["keywords"][category] = []

        total_matches = 0
        processed_items = 0

        for table_name in tables:
            print(f"\n🔍 [TABLE] Menganalisa tabel: {table_name}")

            # Cek apakah sudah mencapai limit dalam quick mode
            if self.quick_mode and len(self.results["raw_data"]) >= self.max_items:
                print(
                    f"   ⚡ [QUICK MODE] Mencapai limit {self.max_items} item - skip tabel ini"
                )
                break

            table_matches = self._search_in_table(table_name)

            table_total = sum(len(matches) for matches in table_matches.values())
            total_matches += table_total
            processed_items += table_total

            if table_total > 0:
                print(f"   ✅ Ditemukan {table_total} hasil")
                # Gabungkan hasil ke kategori yang sesuai
                for category, matches in table_matches.items():
                    if self.quick_mode:
                        # Limit hasil per kategori dalam quick mode
                        remaining_slots = max(
                            0, self.max_items - len(self.results["keywords"][category])
                        )
                        matches = matches[:remaining_slots]

                    self.results["keywords"][category].extend(matches)
                    # Tambahkan ke raw data juga
                    self.results["raw_data"].extend(matches)

                    # Progress indicator
                    if processed_items % 1000 == 0:
                        print(f"   📊 Progress: {processed_items} items processed...")
            else:
                print(f"   ❌ Tidak ada hasil")

        final_count = len(self.results["raw_data"])
        print(f"\n📊 [SUMMARY] Total ditemukan: {final_count} referensi kata kunci")

        if self.quick_mode and final_count >= self.max_items:
            print(f"⚡ [QUICK MODE] Dibatasi sampai {final_count} item untuk performa")

        # Summary per kategori
        for category, matches in self.results["keywords"].items():
            if matches:
                print(
                    f"   📁 {category.title().replace('_', ' ')}: {len(matches)} item"
                )

    def _search_in_table(self, table_name):
        """Cari kata kunci dalam tabel tertentu"""
        cursor = self.conn.cursor()
        category_matches = {category: [] for category in self.target_keywords}

        try:
            # Dapatkan info kolom
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            # Cari untuk setiap kategori
            for category, config in self.target_keywords.items():
                # Buat query pencarian
                search_conditions = []

                # Tambahkan kondisi untuk keywords
                for keyword in config["keywords"]:
                    for col in columns:
                        search_conditions.append(
                            f"LOWER({col}) LIKE '%{keyword.lower()}%'"
                        )

                if search_conditions:
                    query = f"SELECT * FROM {table_name} WHERE {' OR '.join(search_conditions)}"
                    if self.quick_mode:
                        query += f" LIMIT {self.max_items // len(self.target_keywords)}"
                    cursor.execute(query)
                    rows = cursor.fetchall()

                    # Proses hasil
                    for row in rows:
                        match_data = {
                            "table": table_name,
                            "category": category,
                            "columns": columns,
                            "data": {},
                            "matched_keywords": [],
                            "sensitivity": "low",
                        }

                        # Simpan data dan identifikasi kata kunci yang cocok
                        for col, value in zip(columns, row):
                            match_data["data"][col] = value

                            # Cek kata kunci yang cocok
                            if value:
                                value_str = str(value).lower()
                                for keyword in config["keywords"]:
                                    if keyword.lower() in value_str:
                                        if (
                                            keyword
                                            not in match_data["matched_keywords"]
                                        ):
                                            match_data["matched_keywords"].append(
                                                keyword
                                            )

                        # Tentukan tingkat sensitivitas
                        match_data["sensitivity"] = self._determine_sensitivity(
                            match_data
                        )

                        category_matches[category].append(match_data)

        except Exception as e:
            print(f"   ⚠️ Error dalam tabel {table_name} untuk kategori: {e}")

        return category_matches

    def _determine_sensitivity(self, match_data):
        """Tentukan tingkat sensitivitas data"""
        all_text = ""
        for col, value in match_data["data"].items():
            if value:
                all_text += f" {col} {str(value)}"

        all_text = all_text.lower()

        # Cek tingkat sensitivitas
        for keyword in self.sensitive_categories["high_sensitive"]:
            if keyword in all_text:
                return "high"

        for keyword in self.sensitive_categories["medium_sensitive"]:
            if keyword in all_text:
                return "medium"

        return "low"

    def save_category_files(self):
        """Simpan hasil per kategori ke file terpisah"""
        print("\n💾 [SAVE] Menyimpan hasil per kategori...")

        for category, matches in self.results["keywords"].items():
            if not matches:
                continue

            category_dir = self.output_dir / category
            category_file = category_dir / f"{category}_results.json"

            # Group by sensitivity
            high_sens = [m for m in matches if m["sensitivity"] == "high"]
            medium_sens = [m for m in matches if m["sensitivity"] == "medium"]
            low_sens = [m for m in matches if m["sensitivity"] == "low"]

            category_data = {
                "category": category,
                "total_matches": len(matches),
                "sensitivity_breakdown": {
                    "high_sensitive": len(high_sens),
                    "medium_sensitive": len(medium_sens),
                    "low_sensitive": len(low_sens),
                },
                "matched_keywords": list(
                    set([kw for m in matches for kw in m["matched_keywords"]])
                ),
                "results": [],
            }

            # Simpan semua hasil (dengan sensor untuk data sensitif)
            for match in matches:
                match_copy = match.copy()
                # Sensor data sensitif
                if match["sensitivity"] == "high":
                    match_copy["data"] = self._censor_sensitive_data(match["data"])

                category_data["results"].append(match_copy)

            # Simpan ke file
            with open(category_file, "w", encoding="utf-8") as f:
                json.dump(category_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"   📄 {category}: {len(matches)} items → {category_file}")

            # Buat file summary untuk kategori ini
            self._create_category_summary(category, matches, category_dir)

    def _censor_sensitive_data(self, data_dict):
        """Sensor data sensitif"""
        censored = {}
        for key, value in data_dict.items():
            if value is None:
                censored[key] = None
                continue

            value_str = str(value)
            key_lower = key.lower()

            # Cek apakah key mengandung kata sensitif
            if any(
                sens in key_lower
                for sens in self.sensitive_categories["high_sensitive"]
            ):
                if len(value_str) > 20:
                    censored[key] = (
                        f"{value_str[:10]}***[SENSITIVE DATA CENSORED]***{value_str[-5:]}"
                    )
                elif len(value_str) > 10:
                    censored[key] = f"{value_str[:5]}***[CENSORED]***"
                else:
                    censored[key] = "***[CENSORED]***"
            else:
                censored[key] = value

        return censored

    def _create_category_summary(self, category, matches, category_dir):
        """Buat file summary untuk kategori"""
        summary_file = category_dir / f"{category}_summary.txt"

        # Hitung statistik
        total_matches = len(matches)
        high_sens = len([m for m in matches if m["sensitivity"] == "high"])
        medium_sens = len([m for m in matches if m["sensitivity"] == "medium"])
        low_sens = len([m for m in matches if m["sensitivity"] == "low"])

        # Hitung tabel yang terlibat
        tables_involved = set([m["table"] for m in matches])

        # Hitung keywords yang ditemukan
        all_keywords = set()
        for match in matches:
            all_keywords.update(match["matched_keywords"])

        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"CATEGORY SUMMARY: {category.upper()}\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Matches: {total_matches}\n")
            f.write(f"High Sensitive: {high_sens}\n")
            f.write(f"Medium Sensitive: {medium_sens}\n")
            f.write(f"Low Sensitive: {low_sens}\n\n")

            f.write(f"Tables Involved: {len(tables_involved)}\n")
            for table in sorted(tables_involved):
                table_matches = len([m for m in matches if m["table"] == table])
                f.write(f"  - {table}: {table_matches} matches\n")

            f.write(f"\nKeywords Found: {len(all_keywords)}\n")
            for keyword in sorted(all_keywords):
                keyword_count = len(
                    [m for m in matches if keyword in m["matched_keywords"]]
                )
                f.write(f"  - {keyword}: {keyword_count} occurrences\n")

        print(f"   📋 Summary: {summary_file}")

    def create_tree_structure(self):
        """Buat struktur tree-like untuk navigasi"""
        tree_file = self.output_dir / "tree_structure.txt"

        with open(tree_file, "w", encoding="utf-8") as f:
            f.write("ANALYSIS OUTPUT TREE STRUCTURE\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"📁 {self.output_dir.name}/\n")

            # Summary folder
            f.write("├── 📁 summary/\n")
            f.write("│   ├── 📄 overall_summary.json\n")
            f.write("│   ├── 📄 security_report.txt\n")
            f.write("│   └── 📄 statistics.txt\n")

            # Reports folder
            f.write("├── 📁 reports/\n")
            f.write("│   ├── 📄 detailed_report.html\n")
            f.write("│   └── 📄 quick_report.txt\n")

            # Data folder
            f.write("├── 📁 data/\n")
            f.write("│   ├── 📄 raw_export.json\n")
            f.write("│   └── 📄 credentials_summary.json\n")

            # Category folders
            for category in sorted(self.target_keywords.keys()):
                matches = self.results["keywords"].get(category, [])
                if matches:
                    f.write(f"├── 📁 {category}/\n")
                    f.write(f"│   ├── 📄 {category}_results.json\n")
                    f.write(f"│   └── 📄 {category}_summary.txt\n")

            f.write("└── 📄 tree_structure.txt\n\n")

            # Statistics
            total_files = 4  # summary files
            total_files += 2  # report files
            total_files += 2  # data files
            for category in self.target_keywords.keys():
                if self.results["keywords"].get(category):
                    total_files += 2  # category files

            f.write("STATISTICS:\n")
            f.write(f"- Total Categories: {len(self.target_keywords)}\n")
            f.write(
                f"- Categories with Data: {len([c for c in self.target_keywords.keys() if self.results['keywords'].get(c)])}\n"
            )
            f.write(f"- Total Files Created: {total_files}\n")
            f.write(f"- Total Data Matches: {len(self.results['raw_data'])}\n")

        print(f"📋 [TREE] Struktur tree dibuat: {tree_file}")

    def create_overall_summary(self):
        """Buat summary keseluruhan"""
        summary_dir = self.output_dir / "summary"
        summary_file = summary_dir / "overall_summary.json"

        # Hitung statistik keseluruhan
        total_matches = len(self.results["raw_data"])
        high_sensitive = len(
            [m for m in self.results["raw_data"] if m.get("sensitivity") == "high"]
        )
        medium_sensitive = len(
            [m for m in self.results["raw_data"] if m.get("sensitivity") == "medium"]
        )
        low_sensitive = total_matches - high_sensitive - medium_sensitive

        # Hitung per kategori
        category_stats = {}
        for category, matches in self.results["keywords"].items():
            if matches:
                cat_high = len([m for m in matches if m["sensitivity"] == "high"])
                cat_medium = len([m for m in matches if m["sensitivity"] == "medium"])
                cat_low = len([m for m in matches if m["sensitivity"] == "low"])

                category_stats[category] = {
                    "total": len(matches),
                    "high_sensitive": cat_high,
                    "medium_sensitive": cat_medium,
                    "low_sensitive": cat_low,
                    "percentage": (
                        (len(matches) / total_matches * 100) if total_matches > 0 else 0
                    ),
                }

        summary_data = {
            "analysis_info": {
                "database_file": self.db_path,
                "analysis_date": datetime.now().isoformat(),
                "quick_mode": self.quick_mode,
                "max_items_limit": self.max_items if self.quick_mode else None,
            },
            "overall_statistics": {
                "total_matches": total_matches,
                "high_sensitive": high_sensitive,
                "medium_sensitive": medium_sensitive,
                "low_sensitive": low_sensitive,
                "categories_with_data": len([c for c in category_stats.keys()]),
                "total_categories": len(self.target_keywords),
            },
            "category_breakdown": category_stats,
            "top_keywords": self._get_top_keywords(),
            "security_warnings": self._generate_security_warnings(),
        }

        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"📊 [SUMMARY] Overall summary dibuat: {summary_file}")

    def _get_top_keywords(self):
        """Dapatkan keywords terbanyak"""
        keyword_counts = defaultdict(int)

        for match in self.results["raw_data"]:
            for keyword in match["matched_keywords"]:
                keyword_counts[keyword] += 1

        # Sort by count descending
        sorted_keywords = sorted(
            keyword_counts.items(), key=lambda x: x[1], reverse=True
        )
        return dict(sorted_keywords[:10])  # Top 10

    def _generate_security_warnings(self):
        """Generate peringatan keamanan"""
        warnings = []

        high_sensitive = len(
            [m for m in self.results["raw_data"] if m.get("sensitivity") == "high"]
        )

        if high_sensitive > 0:
            warnings.append(f"🚨 Ditemukan {high_sensitive} data highly sensitive")

        if high_sensitive > 10:
            warnings.append(
                "⚠️  Banyak data kredensial ditemukan - pertimbangkan untuk membersihkan"
            )

        tokens_found = any(
            "token" in str(m.get("matched_keywords", []))
            for m in self.results["raw_data"]
        )
        if tokens_found:
            warnings.append(
                "🔑 Token terdeteksi - pastikan tidak terbagi secara publik"
            )

        return warnings

    def create_security_report(self):
        """Buat laporan keamanan"""
        reports_dir = self.output_dir / "reports"
        security_file = reports_dir / "security_report.txt"

        total_matches = len(self.results["raw_data"])
        high_sensitive = len(
            [m for m in self.results["raw_data"] if m.get("sensitivity") == "high"]
        )
        medium_sensitive = len(
            [m for m in self.results["raw_data"] if m.get("sensitivity") == "medium"]
        )

        with open(security_file, "w", encoding="utf-8") as f:
            f.write("SECURITY REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Database: {self.db_path}\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Items Analyzed: {total_matches}\n\n")

            f.write("SENSITIVITY LEVELS:\n")
            f.write("-" * 20 + "\n")
            high_percentage = (
                (high_sensitive / total_matches * 100) if total_matches > 0 else 0
            )
            medium_percentage = (
                (medium_sensitive / total_matches * 100) if total_matches > 0 else 0
            )
            f.write(f"🔴 High Sensitive: {high_sensitive} ({high_percentage:.1f}%)\n")
            f.write(
                f"🟡 Medium Sensitive: {medium_sensitive} ({medium_percentage:.1f}%)\n"
            )
            f.write(
                f"🟢 Low Sensitive: {total_matches - high_sensitive - medium_sensitive}\n\n"
            )

            f.write("CATEGORY BREAKDOWN:\n")
            f.write("-" * 20 + "\n")
            for category, matches in sorted(
                self.results["keywords"].items(), key=lambda x: len(x[1]), reverse=True
            ):
                if matches:
                    high_in_cat = len(
                        [m for m in matches if m.get("sensitivity") == "high"]
                    )
                    f.write(
                        f"• {category.title().replace('_', ' ')}: {len(matches)} total ({high_in_cat} high sensitive)\n"
                    )

            f.write("\nSECURITY RECOMMENDATIONS:\n")
            f.write("-" * 25 + "\n")
            if high_sensitive > 0:
                f.write("⚠️  HIGHLY SENSITIVE DATA DETECTED!\n")
                f.write("   - Ensure this file is stored securely\n")
                f.write("   - Do not share publicly\n")
                f.write("   - Consider data cleanup if necessary\n\n")

            if high_sensitive > 10:
                f.write("🚨 LARGE AMOUNT OF CREDENTIALS FOUND!\n")
                f.write("   - Review and clean sensitive data\n")
                f.write("   - Implement proper data handling procedures\n\n")

            tokens_found = any(
                "token" in str(m.get("matched_keywords", []))
                for m in self.results["raw_data"]
            )
            if tokens_found:
                f.write("🔑 AUTHENTICATION TOKENS DETECTED!\n")
                f.write("   - Ensure tokens are not expired\n")
                f.write("   - Never commit to public repositories\n\n")

            f.write("GENERAL SECURITY TIPS:\n")
            f.write("- Store analysis results in secure locations\n")
            f.write("- Use encryption for sensitive data\n")
            f.write("- Regularly audit and clean old data\n")

        print(f"🔒 [SECURITY] Security report dibuat: {security_file}")

    def create_html_report(self):
        """Buat laporan HTML yang mudah dibaca"""
        reports_dir = self.output_dir / "reports"
        html_file = reports_dir / "detailed_report.html"

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Advanced Keyword Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .category {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .high-sensitive {{ background-color: #f8d7da; border-color: #dc3545; }}
        .medium-sensitive {{ background-color: #fff3cd; border-color: #ffc107; }}
        .low-sensitive {{ background-color: #d1ecf1; border-color: #17a2b8; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #007bff; color: white; }}
        .tree {{ font-family: monospace; background: #f8f9fa; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Advanced Keyword Analysis Report</h1>

        <div class="summary">
            <h2>📊 Analysis Summary</h2>
            <div class="stats">
                <div class="stat">
                    <h3>{len(self.results['raw_data'])}</h3>
                    <p>Total Matches</p>
                </div>
                <div class="stat">
                    <h3>{len([m for m in self.results['raw_data'] if m.get('sensitivity') == 'high'])}</h3>
                    <p>High Sensitive</p>
                </div>
                <div class="stat">
                    <h3>{len(self.target_keywords)}</h3>
                    <p>Categories</p>
                </div>
                <div class="stat">
                    <h3>{datetime.now().strftime('%Y-%m-%d')}</h3>
                    <p>Analysis Date</p>
                </div>
            </div>
        </div>

        <h2>📂 Category Breakdown</h2>
"""

        for category, matches in sorted(
            self.results["keywords"].items(), key=lambda x: len(x[1]), reverse=True
        ):
            if not matches:
                continue

            high_in_cat = len([m for m in matches if m["sensitivity"] == "high"])
            medium_in_cat = len([m for m in matches if m["sensitivity"] == "medium"])
            low_in_cat = len([m for m in matches if m["sensitivity"] == "low"])

            sensitivity_class = "low-sensitive"
            if high_in_cat > 0:
                sensitivity_class = "high-sensitive"
            elif medium_in_cat > 0:
                sensitivity_class = "medium-sensitive"

            html_content += f"""
        <div class="category {sensitivity_class}">
            <h3>{category.title().replace('_', ' ').upper()}</h3>
            <p><strong>Total Items:</strong> {len(matches)}</p>
            <p><strong>High Sensitive:</strong> {high_in_cat}</p>
            <p><strong>Medium Sensitive:</strong> {medium_in_cat}</p>
            <p><strong>Low Sensitive:</strong> {low_in_cat}</p>
            <p><strong>Keywords:</strong> {', '.join(set([kw for m in matches for kw in m['matched_keywords']]))}</p>
        </div>
"""

        html_content += """
        <h2>📋 File Structure</h2>
        <div class="tree">
"""

        # Add tree structure
        tree_content = f"""📁 {self.output_dir.name}/
├── 📁 summary/
│   ├── 📄 overall_summary.json
│   ├── 📄 security_report.txt
│   └── 📄 statistics.txt
├── 📁 reports/
│   ├── 📄 detailed_report.html
│   └── 📄 quick_report.txt
├── 📁 data/
│   ├── 📄 raw_export.json
│   └── 📄 credentials_summary.json"""

        for category in sorted(self.target_keywords.keys()):
            if self.results["keywords"].get(category):
                tree_content += f"""
├── 📁 {category}/
│   ├── 📄 {category}_results.json
│   └── 📄 {category}_summary.txt"""

        tree_content += f"""
└── 📄 tree_structure.txt"""

        html_content += f"<pre>{tree_content}</pre>"
        html_content += """
        </div>
    </div>
</body>
</html>
"""

        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"🌐 [HTML] Detailed HTML report dibuat: {html_file}")

    def run_analysis(self):
        """Jalankan analisis lengkap"""
        print("🎯 [ADVANCED ANALYZER] Script Analisis Kata Kunci Advanced")
        print("=" * 60)
        print(
            "🔍 Target: token, max mode, kredensial, status akun, pro plan, pro trial"
        )
        print("=" * 60)

        # Koneksi ke database terlebih dahulu
        if not self.connect():
            print("❌ [ERROR] Tidak dapat terhubung ke database")
            return False

        try:
            # 1. Buat struktur output
            self.create_output_structure()

            # 2. Cari semua kata kunci
            self.search_keywords()

            if len(self.results["raw_data"]) == 0:
                print("\n❌ [RESULT] Tidak ada kata kunci target ditemukan")
                return

            # 3. Simpan hasil per kategori
            self.save_category_files()

            # 4. Buat summary keseluruhan
            self.create_overall_summary()

            # 5. Buat laporan keamanan
            self.create_security_report()

            # 6. Buat laporan HTML
            self.create_html_report()

            # 7. Buat struktur tree
            self.create_tree_structure()

            print("\n🎉 [COMPLETED] Analisis selesai!")
            print(f"📁 Output tersimpan di: {self.output_dir}")
            print(
                f"🌐 Buka laporan HTML: {self.output_dir}/reports/detailed_report.html"
            )

        except Exception as e:
            print(f"❌ [ERROR] Terjadi kesalahan: {e}")
            return False

        finally:
            self.close()

        return True


def main():
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
        print("📍 [USAGE] python advanced_analyzer.py [path_to_state.vscdb] [--quick]")
        return

    print(f"🗃️  [DATABASE] Menggunakan file: {db_path}")

    # Cek mode quick
    quick_mode = "--quick" in sys.argv
    max_items = 1000 if quick_mode else 5000

    # Inisialisasi analyzer
    analyzer = AdvancedKeywordAnalyzer(
        db_path, quick_mode=quick_mode, max_items=max_items
    )

    # Jalankan analisis
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
