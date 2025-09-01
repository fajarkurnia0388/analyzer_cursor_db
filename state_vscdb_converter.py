#!/usr/bin/env python3
"""
Script untuk mengkonversi seluruh isi database state.vscdb menjadi format yang mudah dibaca.
Output berupa folder dengan nama file database (tanpa ekstensi), berisi banyak folder dan file hasil ekstraksi.
Author: AI Assistant
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import base64


class StateVscdbConverter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.output_dir = None
        self.conn = None
        self.stats = {"tables": 0, "total_rows": 0, "total_files": 0}

    def connect(self):
        """Koneksi ke database SQLite"""
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
        """Tutup koneksi database"""
        if self.conn:
            self.conn.close()

    def get_tables(self):
        """Dapatkan daftar semua tabel dalam database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in cursor.fetchall()]
        return tables

    def create_output_structure(self):
        """Buat folder output dengan nama file database tanpa ekstensi"""
        base_name = Path(self.db_path).stem
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"{base_name}_converted_{timestamp}")
        self.output_dir.mkdir(exist_ok=True)

        # Buat folder untuk setiap tabel
        tables = self.get_tables()
        for table in tables:
            (self.output_dir / table).mkdir(exist_ok=True)

        # Buat folder summary
        (self.output_dir / "summary").mkdir(exist_ok=True)
        (self.output_dir / "reports").mkdir(exist_ok=True)

        print(f"📁 [OUTPUT] Folder output dibuat: {self.output_dir}")

    def process_value(self, value):
        """Proses nilai untuk membuatnya mudah dibaca"""
        if value is None:
            return None
        elif isinstance(value, bytes):
            # Coba decode sebagai UTF-8
            try:
                decoded = value.decode("utf-8")
                # Jika terlihat seperti JSON, parse it
                if decoded.strip().startswith(("{", "[")):
                    try:
                        return json.loads(decoded)
                    except:
                        pass
                return decoded
            except UnicodeDecodeError:
                # Jika gagal decode, encode sebagai base64
                return (
                    f"[BINARY DATA - BASE64]: {base64.b64encode(value).decode('ascii')}"
                )
        elif isinstance(value, str):
            # Coba parse sebagai JSON jika terlihat seperti JSON
            if value.strip().startswith(("{", "[")):
                try:
                    return json.loads(value)
                except:
                    pass
            return value
        else:
            return value

    def export_table_data(self, table_name):
        """Ekspor seluruh isi tabel ke file JSON"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]

            data_list = []
            for row in rows:
                row_dict = {}
                for col, val in zip(columns, row):
                    row_dict[col] = self.process_value(val)
                data_list.append(row_dict)

            # Simpan ke file JSON
            table_dir = self.output_dir / table_name
            output_file = table_dir / f"{table_name}_data.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(data_list, f, indent=2, ensure_ascii=False, default=str)

            print(
                f"   📄 Tabel '{table_name}' diekspor ke {output_file} ({len(data_list)} baris)"
            )

            # Update statistik
            self.stats["total_rows"] += len(data_list)
            self.stats["total_files"] += 1

            return len(data_list)

        except Exception as e:
            print(f"❌ [ERROR] Gagal ekspor tabel {table_name}: {e}")
            return 0

    def export_table_schema(self, table_name):
        """Ekspor schema tabel"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            schema = cursor.fetchall()

            schema_data = []
            for col in schema:
                schema_data.append(
                    {
                        "cid": col[0],
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "dflt_value": col[4],
                        "pk": bool(col[5]),
                    }
                )

            table_dir = self.output_dir / table_name
            schema_file = table_dir / f"{table_name}_schema.json"
            with open(schema_file, "w", encoding="utf-8") as f:
                json.dump(schema_data, f, indent=2, ensure_ascii=False)

            print(f"   📋 Schema tabel '{table_name}' diekspor ke {schema_file}")

        except Exception as e:
            print(f"❌ [ERROR] Gagal ekspor schema {table_name}: {e}")

    def export_table_summary(self, table_name, row_count):
        """Buat file summary untuk tabel"""
        cursor = self.conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()

            summary_data = {
                "table_name": table_name,
                "total_rows": row_count,
                "columns_count": len(columns),
                "columns": [{"name": col[1], "type": col[2]} for col in columns],
                "exported_at": datetime.now().isoformat(),
            }

            table_dir = self.output_dir / table_name
            summary_file = table_dir / f"{table_name}_summary.txt"
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"SUMMARY: {table_name.upper()}\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Total Rows: {row_count}\n")
                f.write(f"Total Columns: {len(columns)}\n\n")
                f.write("COLUMNS:\n")
                f.write("-" * 20 + "\n")
                for col in columns:
                    f.write(f"• {col[1]} ({col[2]})\n")
                f.write(
                    f"\nExported at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )

            print(f"   📋 Summary tabel '{table_name}' dibuat")

        except Exception as e:
            print(f"❌ [ERROR] Gagal buat summary {table_name}: {e}")

    def create_database_summary(self):
        """Buat summary keseluruhan database"""
        tables = self.get_tables()
        summary_data = {
            "database_file": self.db_path,
            "export_date": datetime.now().isoformat(),
            "total_tables": len(tables),
            "total_rows": self.stats["total_rows"],
            "total_files": self.stats["total_files"],
            "tables": [],
        }

        for table in tables:
            table_dir = self.output_dir / table
            data_file = table_dir / f"{table}_data.json"
            if data_file.exists():
                with open(data_file, "r", encoding="utf-8") as f:
                    try:
                        data = json.load(f)
                        row_count = len(data)
                    except:
                        row_count = 0
            else:
                row_count = 0

            summary_data["tables"].append(
                {
                    "name": table,
                    "rows": row_count,
                    "data_file": str(data_file),
                    "schema_file": str(table_dir / f"{table}_schema.json"),
                    "summary_file": str(table_dir / f"{table}_summary.txt"),
                }
            )

        summary_file = self.output_dir / "summary" / "database_summary.json"
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)

        print(f"📊 [SUMMARY] Database summary dibuat: {summary_file}")

    def create_html_report(self):
        """Buat laporan HTML untuk navigasi"""
        tables = self.get_tables()
        html_content = f"""
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Database Export Report - {Path(self.db_path).name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .table-item {{ margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .stats {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .stat {{ text-align: center; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #007bff; color: white; }}
        .file-link {{ color: #007bff; text-decoration: none; }}
        .file-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🗃️ Database Export Report</h1>
        <p><strong>File:</strong> {Path(self.db_path).name}</p>
        <p><strong>Exported:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

        <div class="summary">
            <h2>📊 Summary</h2>
            <div class="stats">
                <div class="stat">
                    <h3>{len(tables)}</h3>
                    <p>Tables</p>
                </div>
                <div class="stat">
                    <h3>{self.stats['total_rows']:,}</h3>
                    <p>Total Rows</p>
                </div>
                <div class="stat">
                    <h3>{self.stats['total_files']}</h3>
                    <p>Files Created</p>
                </div>
            </div>
        </div>

        <h2>📋 Tables Overview</h2>
        <table>
            <tr>
                <th>Table Name</th>
                <th>Rows</th>
                <th>Data File</th>
                <th>Schema File</th>
                <th>Summary File</th>
            </tr>"""

        for table in tables:
            table_dir = self.output_dir / table
            data_file = table_dir / f"{table}_data.json"
            schema_file = table_dir / f"{table}_schema.json"
            summary_file = table_dir / f"{table}_summary.txt"

            # Hitung jumlah baris
            row_count = 0
            if data_file.exists():
                try:
                    with open(data_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        row_count = len(data)
                except:
                    row_count = 0

            html_content += f"""
            <tr>
                <td><strong>{table}</strong></td>
                <td>{row_count:,}</td>
                <td><a href="{data_file.name}" class="file-link">📄 {table}_data.json</a></td>
                <td><a href="{schema_file.name}" class="file-link">📋 {table}_schema.json</a></td>
                <td><a href="{summary_file.name}" class="file-link">📋 {table}_summary.txt</a></td>
            </tr>"""

        html_content += """
        </table>

        <h2>📁 File Structure</h2>
        <div style="font-family: monospace; background: #f8f9fa; padding: 15px; border-radius: 5px;">
"""

        # Buat struktur tree
        tree_content = f"""📁 {self.output_dir.name}/
├── 📁 summary/
│   └── 📄 database_summary.json
├── 📁 reports/
│   └── 📄 export_report.html"""

        for table in tables:
            tree_content += f"""
├── 📁 {table}/
│   ├── 📄 {table}_data.json
│   ├── 📄 {table}_schema.json
│   └── 📄 {table}_summary.txt"""

        html_content += f"<pre>{tree_content}</pre>"
        html_content += """
        </div>
    </div>
</body>
</html>"""

        html_file = self.output_dir / "reports" / "export_report.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"🌐 [HTML] Laporan HTML dibuat: {html_file}")

    def run_conversion(self):
        """Jalankan proses konversi seluruh isi database"""
        print("🔄 [CONVERTER] Script Konversi Database Lengkap")
        print("=" * 50)
        print(f"📁 Target: {Path(self.db_path).name}")
        print("=" * 50)

        if not self.connect():
            return False

        self.create_output_structure()

        tables = self.get_tables()
        self.stats["tables"] = len(tables)
        print(f"📋 [INFO] Menemukan {len(tables)} tabel: {', '.join(tables)}")

        for table in tables:
            print(f"\n🔄 [TABLE] Memproses tabel: {table}")
            row_count = self.export_table_data(table)
            self.export_table_schema(table)
            self.export_table_summary(table, row_count)

        # Buat file summary dan laporan
        self.create_database_summary()
        self.create_html_report()

        self.close()

        print("\n🎉 [COMPLETED] Konversi selesai!")
        print(f"📁 Output tersimpan di: {self.output_dir}")
        print(f"📊 Total tabel: {self.stats['tables']}")
        print(f"📊 Total baris: {self.stats['total_rows']:,}")
        print(f"📊 Total file: {self.stats['total_files']}")
        print(f"🌐 Buka laporan: {self.output_dir}/reports/export_report.html")

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
        print("📍 [USAGE] python state_vscdb_converter.py [path_to_state.vscdb]")
        return

    print(f"🗃️  [DATABASE] Menggunakan file: {db_path}")

    converter = StateVscdbConverter(db_path)
    converter.run_conversion()


if __name__ == "__main__":
    main()
