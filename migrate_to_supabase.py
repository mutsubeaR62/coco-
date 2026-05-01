"""
既存のJSONファイルをSupabaseに移行するスクリプト
一度だけ実行してください。
"""
import json
import os
import sys
import tomllib

# secrets.tomlからSupabase接続情報を読み込む
secrets_path = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
with open(secrets_path, "rb") as f:
    secrets = tomllib.load(f)

url = secrets["supabase"]["url"]
key = secrets["supabase"]["key"]

from supabase import create_client
sb = create_client(url, key)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

files = [
    "users.json",
    "products.json",
    "shift_requests.json",
    "shift_schedules.json",
    "progress.json",
    "checklists.json",
    "stepup_data.json",
    "manual.json",
    "store_settings.json",
    "file_attachments.json",
]

print("=== Supabase移行開始 ===\n")
for fname in files:
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        print(f"⏭️  スキップ（ファイルなし）: {fname}")
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sb.table("json_store").upsert({"key": fname, "data": data}).execute()
    print(f"✅ 移行完了: {fname}")

print("\n=== 移行完了！ ===")
