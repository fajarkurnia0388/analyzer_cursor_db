#!/usr/bin/env python3
"""
Script khusus untuk menganalisa berbagai kata kunci penting di file state.vscdb
Fokus pada: token, max mode, kredensial, status akun, pro plan, pro trial, dll
Author: AI Assistant
"""

import sqlite3
import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import re

class KeywordAnalyzer:
    def __init__(self, db_path, quick_mode=False, max_items=1000):
        self.db_path = db_path
        self.conn = None
        self.quick_mode = quick_mode
        self.max_items = max_items
        self.results = {
            'keywords': {},
            'summary': {},
            'raw_data': []
        }
        
        # Daftar kata kunci penting untuk dianalisa
        self.target_keywords = {
            'authentication': {
                'keywords': ['token', 'auth', 'login', 'logout', 'credential', 'password', 'session'],
                'patterns': [
                    r'token', r'auth.*token', r'access.*token', r'refresh.*token',
                    r'credential', r'auth.*key', r'api.*key', r'login', r'logout',
                    r'session', r'password', r'bearer'
                ]
            },
            'subscription': {
                'keywords': ['pro', 'plan', 'subscription', 'trial', 'premium', 'paid', 'billing'],
                'patterns': [
                    r'pro.*plan', r'pro.*trial', r'subscription', r'premium',
                    r'billing', r'paid', r'trial.*end', r'plan.*type',
                    r'membership', r'upgrade', r'downgrade'
                ]
            },
            'ai_features': {
                'keywords': ['max mode', 'ai', 'model', 'chat', 'composer', 'copilot'],
                'patterns': [
                    r'max.*mode', r'ai.*model', r'chat.*model', r'composer',
                    r'copilot', r'code.*generation', r'ai.*feature'
                ]
            },
            'account_status': {
                'keywords': ['status', 'active', 'inactive', 'enabled', 'disabled', 'banned'],
                'patterns': [
                    r'account.*status', r'user.*status', r'active', r'inactive',
                    r'enabled', r'disabled', r'banned', r'suspended'
                ]
            },
            'blackbox_specific': {
                'keywords': ['blackbox', 'blackboxai', 'blackboxapp'],
                'patterns': [
                    r'blackbox.*agent', r'blackbox.*auth', r'blackbox.*user',
                    r'blackbox.*api', r'blackbox.*key', r'blackbox.*pro'
                ]
            },
            'usage_limits': {
                'keywords': ['limit', 'quota', 'usage', 'remaining', 'consumed'],
                'patterns': [
                    r'usage.*limit', r'quota', r'remaining.*usage', r'consumed',
                    r'rate.*limit', r'api.*limit'
                ]
            }
        }
        
        # Kategori data sensitif
        self.sensitive_categories = {
            'high_sensitive': ['token', 'password', 'key', 'secret', 'credential'],
            'medium_sensitive': ['userid', 'email', 'api', 'auth'],
            'low_sensitive': ['plan', 'status', 'mode', 'feature']
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
            print(f"📊 [INFO] Ukuran file: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
            
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

    def search_keywords(self):
        """Cari semua kata kunci target dalam database"""
        if self.quick_mode:
            print(f"\n⚡ [QUICK SEARCH] Mode cepat - maksimal {self.max_items} hasil per kategori")
        else:
            print("\n🔍 [SEARCH] Mencari kata kunci target...")
        
        tables = self.get_tables()
        print(f"📋 [INFO] Menganalisa {len(tables)} tabel: {', '.join(tables)}")
        
        # Inisialisasi hasil untuk setiap kategori
        for category in self.target_keywords:
            self.results['keywords'][category] = []
        
        total_matches = 0
        processed_items = 0
        
        for table_name in tables:
            print(f"\n🔍 [TABLE] Menganalisa tabel: {table_name}")
            
            # Cek apakah sudah mencapai limit dalam quick mode
            if self.quick_mode and len(self.results['raw_data']) >= self.max_items:
                print(f"   ⚡ [QUICK MODE] Mencapai limit {self.max_items} item - skip tabel ini")
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
                        remaining_slots = max(0, self.max_items - len(self.results['keywords'][category]))
                        matches = matches[:remaining_slots]
                    
                    self.results['keywords'][category].extend(matches)
                    # Tambahkan ke raw data juga
                    self.results['raw_data'].extend(matches)
                    
                    # Progress indicator
                    if processed_items % 1000 == 0:
                        print(f"   📊 Progress: {processed_items} items processed...")
            else:
                print(f"   ❌ Tidak ada hasil")
        
        final_count = len(self.results['raw_data'])
        print(f"\n📊 [SUMMARY] Total ditemukan: {final_count} referensi kata kunci")
        
        if self.quick_mode and final_count >= self.max_items:
            print(f"⚡ [QUICK MODE] Dibatasi sampai {final_count} item untuk performa")
        
        # Summary per kategori
        for category, matches in self.results['keywords'].items():
            if matches:
                print(f"   📁 {category.title().replace('_', ' ')}: {len(matches)} item")

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
                for keyword in config['keywords']:
                    for col in columns:
                        search_conditions.append(f"LOWER({col}) LIKE '%{keyword.lower()}%'")
                
                if search_conditions:
                    query = f"SELECT * FROM {table_name} WHERE {' OR '.join(search_conditions)}"
                    if self.quick_mode:
                        query += f" LIMIT {self.max_items // len(self.target_keywords)}"
                    cursor.execute(query)
                    rows = cursor.fetchall()
                    
                    # Proses hasil
                    for row in rows:
                        match_data = {
                            'table': table_name,
                            'category': category,
                            'columns': columns,
                            'data': {},
                            'matched_keywords': [],
                            'sensitivity': 'low'
                        }
                        
                        # Simpan data dan identifikasi kata kunci yang cocok
                        for col, value in zip(columns, row):
                            match_data['data'][col] = value
                            
                            # Cek kata kunci yang cocok
                            if value:
                                value_str = str(value).lower()
                                for keyword in config['keywords']:
                                    if keyword.lower() in value_str:
                                        if keyword not in match_data['matched_keywords']:
                                            match_data['matched_keywords'].append(keyword)
                        
                        # Tentukan tingkat sensitivitas
                        match_data['sensitivity'] = self._determine_sensitivity(match_data)
                        
                        category_matches[category].append(match_data)
                        
        except Exception as e:
            print(f"   ⚠️ Error dalam tabel {table_name} untuk kategori: {e}")
        
        return category_matches

    def _determine_sensitivity(self, match_data):
        """Tentukan tingkat sensitivitas data"""
        all_text = ""
        for col, value in match_data['data'].items():
            if value:
                all_text += f" {col} {str(value)}"
        
        all_text = all_text.lower()
        
        # Cek tingkat sensitivitas
        for keyword in self.sensitive_categories['high_sensitive']:
            if keyword in all_text:
                return 'high'
        
        for keyword in self.sensitive_categories['medium_sensitive']:
            if keyword in all_text:
                return 'medium'
        
        return 'low'

    def analyze_patterns(self):
        """Analisis pattern dari kata kunci yang ditemukan"""
        if self.quick_mode:
            print("\n⚡ [PATTERN ANALYSIS] Quick mode - analisis pattern dilewati untuk performa")
            return {}
            
        print("\n🔬 [PATTERN ANALYSIS] Menganalisis pola kata kunci...")
        
        pattern_results = {}
        
        for category, config in self.target_keywords.items():
            print(f"\n📂 [CATEGORY] {category.title().replace('_', ' ')}")
            pattern_results[category] = {}
            
            # Analisis pattern untuk kategori ini
            matches = self.results['keywords'][category]
            if not matches:
                print(f"   ❌ Tidak ada data untuk dianalisis")
                continue
            
            # Batasi analisis pattern untuk performa
            sample_matches = matches[:100] if len(matches) > 100 else matches
            if len(matches) > 100:
                print(f"   ⚡ Menganalisis sample 100 dari {len(matches)} items untuk performa")
            
            # Analisis pattern regex (hanya 3 pattern pertama untuk performa)
            for pattern in config['patterns'][:3]:
                pattern_matches = []
                for match in sample_matches:
                    all_text = ""
                    for col, value in match['data'].items():
                        if value:
                            all_text += f" {str(value)}"
                    
                    if re.search(pattern, all_text, re.IGNORECASE):
                        pattern_matches.append(match)
                
                if pattern_matches:
                    pattern_results[category][pattern] = len(pattern_matches)
                    print(f"   🔍 Pattern '{pattern}': {len(pattern_matches)} matches")
            
            # Summary untuk kategori
            total_category_matches = len(matches)
            high_sensitive = len([m for m in matches if m['sensitivity'] == 'high'])
            medium_sensitive = len([m for m in matches if m['sensitivity'] == 'medium'])
            
            print(f"   📊 Total: {total_category_matches} | High: {high_sensitive} | Medium: {medium_sensitive}")
        
        return pattern_results

    def extract_credentials_info(self):
        """Extract informasi kredensial spesifik"""
        print("\n🔐 [CREDENTIALS] Mengekstrak informasi kredensial...")
        
        credentials_info = {
            'tokens': [],
            'api_keys': [],
            'user_ids': [],
            'subscription_info': [],
            'account_status': []
        }
        
        # Batasi data yang diproses untuk quick mode
        data_to_process = self.results['raw_data']
        if self.quick_mode and len(data_to_process) > 200:
            data_to_process = data_to_process[:200]
            print(f"   ⚡ [QUICK MODE] Menganalisis 200 item pertama dari {len(self.results['raw_data'])} untuk performa")
        
        for i, match in enumerate(data_to_process):
            # Progress indicator untuk dataset besar
            if i % 100 == 0 and i > 0:
                print(f"   📊 Progress: {i}/{len(data_to_process)} items processed...")
                
            # Cek untuk tokens
            for col, value in match['data'].items():
                if value and isinstance(value, str):
                    # Parse JSON jika memungkinkan
                    try:
                        if value.strip().startswith('{'):
                            json_data = json.loads(value)
                            
                            # Extract token info
                            self._extract_from_json(json_data, credentials_info, match['table'])
                            
                    except:
                        # Cek sebagai string biasa
                        self._extract_from_string(col, value, credentials_info, match['table'])
        
        # Tampilkan hasil
        for cred_type, items in credentials_info.items():
            if items:
                print(f"   🔑 {cred_type.title().replace('_', ' ')}: {len(items)} items")
        
        return credentials_info

    def _extract_from_json(self, json_data, credentials_info, table_name):
        """Extract informasi dari data JSON"""
        if isinstance(json_data, dict):
            for key, value in json_data.items():
                key_lower = key.lower()
                
                # Token detection
                if any(keyword in key_lower for keyword in ['token', 'access', 'refresh', 'bearer']):
                    credentials_info['tokens'].append({
                        'key': key,
                        'value_preview': str(value)[:50] + "..." if len(str(value)) > 50 else str(value),
                        'table': table_name,
                        'type': 'token'
                    })
                
                # API Key detection
                elif any(keyword in key_lower for keyword in ['api', 'key', 'secret']):
                    credentials_info['api_keys'].append({
                        'key': key,
                        'value_preview': str(value)[:50] + "..." if len(str(value)) > 50 else str(value),
                        'table': table_name,
                        'type': 'api_key'
                    })
                
                # User ID detection
                elif any(keyword in key_lower for keyword in ['userid', 'user_id', 'uid']):
                    credentials_info['user_ids'].append({
                        'key': key,
                        'value': value,
                        'table': table_name,
                        'type': 'user_id'
                    })
                
                # Subscription info
                elif any(keyword in key_lower for keyword in ['plan', 'subscription', 'trial', 'premium', 'pro']):
                    credentials_info['subscription_info'].append({
                        'key': key,
                        'value': value,
                        'table': table_name,
                        'type': 'subscription'
                    })
                
                # Account status
                elif any(keyword in key_lower for keyword in ['status', 'active', 'enabled']):
                    credentials_info['account_status'].append({
                        'key': key,
                        'value': value,
                        'table': table_name,
                        'type': 'status'
                    })
                
                # Rekursif untuk nested objects
                elif isinstance(value, dict):
                    self._extract_from_json(value, credentials_info, table_name)

    def _extract_from_string(self, col, value, credentials_info, table_name):
        """Extract informasi dari string biasa"""
        col_lower = col.lower()
        value_str = str(value)
        
        # Token detection
        if any(keyword in col_lower for keyword in ['token', 'access', 'refresh']):
            credentials_info['tokens'].append({
                'key': col,
                'value_preview': value_str[:50] + "..." if len(value_str) > 50 else value_str,
                'table': table_name,
                'type': 'token'
            })
        
        # User ID detection
        elif any(keyword in col_lower for keyword in ['userid', 'user_id']):
            credentials_info['user_ids'].append({
                'key': col,
                'value': value,
                'table': table_name,
                'type': 'user_id'
            })

    def display_detailed_results(self, max_items_per_category=3):
        """Tampilkan hasil detail dengan format yang mudah dibaca"""
        print("\n" + "="*80)
        print("📋 [DETAILED RESULTS] HASIL DETAIL ANALISIS KATA KUNCI")
        print("="*80)
        
        for category, matches in self.results['keywords'].items():
            if not matches:
                continue
                
            print(f"\n📂 [KATEGORI] {category.upper().replace('_', ' ')}")
            print("-" * 60)
            print(f"Total item: {len(matches)}")
            
            # Group by sensitivity
            high_sens = [m for m in matches if m['sensitivity'] == 'high']
            medium_sens = [m for m in matches if m['sensitivity'] == 'medium']
            low_sens = [m for m in matches if m['sensitivity'] == 'low']
            
            print(f"🔴 High Sensitive: {len(high_sens)} | 🟡 Medium: {len(medium_sens)} | 🟢 Low: {len(low_sens)}")
            
            # Tampilkan high sensitive items first
            priority_items = high_sens[:max_items_per_category] + medium_sens[:max_items_per_category-len(high_sens[:max_items_per_category])]
            if len(priority_items) < max_items_per_category:
                priority_items.extend(low_sens[:max_items_per_category-len(priority_items)])
            
            for i, match in enumerate(priority_items, 1):
                sensitivity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[match['sensitivity']]
                print(f"\n   📄 [ITEM {i}] {sensitivity_icon} Table: {match['table']}")
                print(f"      🏷️  Matched Keywords: {', '.join(match['matched_keywords'])}")
                
                for col, value in match['data'].items():
                    if value and any(keyword.lower() in str(value).lower() for keyword in match['matched_keywords']):
                        formatted_value = self._format_value(value, match['sensitivity'])
                        print(f"      🔑 {col}:")
                        print(f"         {formatted_value}")
            
            if len(matches) > max_items_per_category:
                print(f"   ⚠️  ... dan {len(matches) - max_items_per_category} item lainnya")

    def _format_value(self, value, sensitivity='low'):
        """Format nilai berdasarkan tingkat sensitivitas"""
        if value is None:
            return "NULL"
        
        value_str = str(value)
        
        # Untuk data high sensitive, sensor sebagian
        if sensitivity == 'high':
            if len(value_str) > 20:
                return f"{value_str[:10]}***[DISENSOR]***{value_str[-5:]}"
            elif len(value_str) > 10:
                return f"{value_str[:5]}***[DISENSOR]***"
        
        # Coba parse sebagai JSON
        try:
            if value_str.strip().startswith(("{", "[")):
                parsed = json.loads(value_str)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                
                if len(formatted) > 600:
                    return formatted[:600] + "\n         ... [JSON DIPOTONG]"
                return formatted
        except:
            pass
        
        # Untuk string biasa
        if len(value_str) > 200:
            return value_str[:200] + " ... [DIPOTONG]"
        
        return value_str

    def export_results(self, output_file=None, include_sensitive=False):
        """Export hasil ke file JSON"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"keyword_analysis_{timestamp}.json"
        
        export_data = {
            'analysis_info': {
                'database_file': self.db_path,
                'analysis_date': datetime.now().isoformat(),
                'total_matches': len(self.results['raw_data']),
                'include_sensitive_data': include_sensitive
            },
            'summary': {
                'categories': {cat: len(matches) for cat, matches in self.results['keywords'].items()}
            },
            'detailed_results': {}
        }
        
        # Export detailed results
        for category, matches in self.results['keywords'].items():
            if matches:
                category_data = []
                for match in matches:
                    # Filter data sensitif jika diperlukan
                    if not include_sensitive and match['sensitivity'] == 'high':
                        match_data = {
                            'table': match['table'],
                            'category': match['category'],
                            'matched_keywords': match['matched_keywords'],
                            'sensitivity': match['sensitivity'],
                            'data': {'[SENSITIVE DATA FILTERED]': 'Use include_sensitive=True to export'}
                        }
                    else:
                        match_data = {
                            'table': match['table'],
                            'category': match['category'],
                            'matched_keywords': match['matched_keywords'],
                            'sensitivity': match['sensitivity'],
                            'data': {}
                        }
                        
                        for col, value in match['data'].items():
                            if isinstance(value, str) and value.strip().startswith(("{", "[")):
                                try:
                                    match_data['data'][col] = json.loads(value)
                                except:
                                    match_data['data'][col] = value
                            else:
                                match_data['data'][col] = value
                    
                    category_data.append(match_data)
                
                export_data['detailed_results'][category] = category_data
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n💾 [EXPORT] Hasil berhasil diexport ke: {output_file}")
            if not include_sensitive:
                print("⚠️  [NOTICE] Data sensitif telah disensor. Gunakan --include-sensitive untuk export lengkap")
            return output_file
        except Exception as e:
            print(f"❌ [ERROR] Gagal export: {e}")
            return None

    def generate_security_report(self):
        """Generate laporan keamanan"""
        print("\n" + "="*80)
        print("🔒 [SECURITY REPORT] LAPORAN KEAMANAN DATA")
        print("="*80)
        
        total_matches = len(self.results['raw_data'])
        high_sensitive = len([m for m in self.results['raw_data'] if m.get('sensitivity') == 'high'])
        medium_sensitive = len([m for m in self.results['raw_data'] if m.get('sensitivity') == 'medium'])
        
        print(f"🗃️  Database: {self.db_path}")
        print(f"📅 Tanggal analisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔍 Total item dianalisis: {total_matches}")
        
        print(f"\n🚨 TINGKAT SENSITIVITAS:")
        high_percentage = (high_sensitive/total_matches*100) if total_matches > 0 else 0
        medium_percentage = (medium_sensitive/total_matches*100) if total_matches > 0 else 0
        print(f"   🔴 High Sensitive: {high_sensitive} ({high_percentage:.1f}%)")
        print(f"   🟡 Medium Sensitive: {medium_sensitive} ({medium_percentage:.1f}%)")
        print(f"   🟢 Low Sensitive: {total_matches - high_sensitive - medium_sensitive}")
        
        print(f"\n📂 Distribusi per kategori:")
        for category, matches in sorted(self.results['keywords'].items(), 
                                      key=lambda x: len(x[1]), reverse=True):
            if matches:
                high_in_cat = len([m for m in matches if m.get('sensitivity') == 'high'])
                print(f"   • {category.title().replace('_', ' ')}: {len(matches)} total ({high_in_cat} high sensitive)")
        
        # Rekomendasi keamanan
        print(f"\n💡 [REKOMENDASI KEAMANAN]")
        if high_sensitive > 0:
            print("   ⚠️  DITEMUKAN data highly sensitive! Pastikan file ini aman")
        if high_sensitive > 10:
            print("   🚨 BANYAK data kredensial ditemukan - pertimbangkan untuk membersihkan")
        if any('token' in str(m.get('matched_keywords', [])) for m in self.results['raw_data']):
            print("   🔑 Token terdeteksi - pastikan tidak terbagi secara publik")
        
        print("="*80)

def main():
    print("🎯 [KEYWORD ANALYZER] Script Analisis Kata Kunci Spesifik")
    print("=" * 60)
    print("🔍 Target: token, max mode, kredensial, status akun, pro plan, pro trial")
    print("=" * 60)
    
    # Tentukan file database dan mode
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_paths = [
        os.path.join(script_dir, "state.vscdb"),
        os.path.join(script_dir, "state(2).vscdb"),
    ]
    
    db_path = None
    quick_mode = False
    
    # Parse arguments
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg in ["--quick", "-q"]:
                quick_mode = True
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
        print("📍 [USAGE] python keyword_analyzer.py [path_to_state.vscdb] [--quick]")
        print("📍 [OPTIONS] --quick atau -q untuk mode cepat (max 1000 items)")
        return
    
    print(f"🗃️  [DATABASE] Menggunakan file: {db_path}")
    
    if not quick_mode:
        print("\n⚡ [MODE SELECTION] Pilih mode analisis:")
        print("1. Mode cepat (⚡ ~30 detik, max 1000 items)")
        print("2. Mode lengkap (🔍 beberapa menit, semua data)")
        choice = input("Pilih mode (1/2): ").strip()
        if choice == "1":
            quick_mode = True
    
    # Inisialisasi analyzer
    if quick_mode:
        print("⚡ [QUICK MODE] Mode cepat aktif - analisis dibatasi untuk performa")
        analyzer = KeywordAnalyzer(db_path, quick_mode=True, max_items=1000)
    else:
        print("🔍 [FULL MODE] Mode lengkap - analisis semua data")
        analyzer = KeywordAnalyzer(db_path, quick_mode=False)
    
    try:
        # Koneksi ke database
        if not analyzer.connect():
            return
        
        # Mulai analisis
        print("\n🚀 [START] Memulai analisis kata kunci...")
        
        # 1. Cari semua kata kunci
        analyzer.search_keywords()
        
        if len(analyzer.results['raw_data']) == 0:
            print("\n❌ [RESULT] Tidak ada kata kunci target ditemukan")
            return
        
        # 2. Analisis pattern
        pattern_results = analyzer.analyze_patterns()
        
        # 3. Extract kredensial info
        credentials_info = analyzer.extract_credentials_info()
        
        # 4. Tampilkan hasil detail
        analyzer.display_detailed_results()
        
        # 5. Generate security report
        analyzer.generate_security_report()
        
        # 6. Export hasil
        print("\n💾 [EXPORT OPTIONS]")
        print("1. Export normal (data sensitif disensor)")
        print("2. Export lengkap (termasuk data sensitif)")
        print("3. Tidak export")
        
        choice = input("Pilih opsi (1/2/3): ").strip()
        
        if choice == "1":
            export_file = analyzer.export_results(include_sensitive=False)
        elif choice == "2":
            confirm = input("⚠️  Export data sensitif? Pastikan file aman! (yes/no): ").lower()
            if confirm in ['yes', 'y']:
                export_file = analyzer.export_results(include_sensitive=True)
            else:
                export_file = analyzer.export_results(include_sensitive=False)
        
        if choice in ["1", "2"] and 'export_file' in locals() and export_file:
            print(f"✅ [SUCCESS] Analisis selesai dan diexport ke: {export_file}")
        
        print("\n🎉 [COMPLETED] Analisis kata kunci selesai!")
        
    except Exception as e:
        print(f"❌ [ERROR] Terjadi kesalahan: {e}")
    
    finally:
        analyzer.close()

if __name__ == "__main__":
    main()
