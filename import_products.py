"""
GoogleスプレッドシートのCSVからproducts.jsonを生成するスクリプト。
使い方: python import_products.py
"""
import csv, json, os, re

DOWNLOADS = os.path.join(os.path.expanduser("~"), "Downloads")
DATA_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def find_csv(keyword):
    for f in os.listdir(DOWNLOADS):
        if keyword in f and f.endswith(".csv"):
            return os.path.join(DOWNLOADS, f)
    return None

def read_csv(path, encoding="utf-8-sig"):
    if not path:
        return []
    for enc in [encoding, "utf-8", "cp932", "shift_jis"]:
        try:
            with open(path, encoding=enc, newline="") as f:
                return list(csv.reader(f))
        except (UnicodeDecodeError, TypeError):
            continue
    return []

def to_int(val):
    try:
        v = float(str(val).replace(",", "").strip())
        return int(v)
    except (ValueError, TypeError):
        return None

# ─── データ用(定数表）を読む ──────────────────────────────────
def load_standards():
    path = find_csv("データ用")
    rows = read_csv(path)
    standards = {}
    for row in rows[1:]:  # 1行目はヘッダー
        if len(row) < 2:
            continue
        name = row[0].strip()
        if not name or name.startswith("#"):
            continue
        default = to_int(row[1]) if len(row) > 1 else None
        friday  = to_int(row[2]) if len(row) > 2 else None
        event   = to_int(row[3]) if len(row) > 3 else None
        if default is not None:
            standards[name] = {"default": default, "friday": friday, "event": event}
    print(f"  定数: {len(standards)}件 読み込み")
    return standards

# ─── 在庫入力（自店オリジナル）を読む ────────────────────────
def load_stock_sheet():
    path = find_csv("在庫入力")
    rows = read_csv(path)
    items = []
    for row in rows[1:]:  # 1行目はヘッダー
        if len(row) < 1:
            continue
        name = row[0].strip()
        if not name or name.startswith("#"):
            continue
        loc  = row[3].strip() if len(row) > 3 else ""
        note = row[2].strip() if len(row) > 2 else ""
        rare = "希少" in (row[7].strip() if len(row) > 7 else "")
        # 場所が空＝セクション見出しなのでスキップ
        if not loc:
            continue
        # 改行を除去してnoteを整理
        note = re.sub(r'\s+', ' ', note).strip()
        items.append({
            "name": name,
            "location": loc,
            "note": note,
            "rare": rare,
        })
    print(f"  在庫入力: {len(items)}件 読み込み")
    return items

# ─── マージしてproducts.jsonを生成 ────────────────────────────
def build_products(standards, stock_items):
    products = []
    seen = set()

    # 在庫入力シートにある商品を基準にする
    for item in stock_items:
        name = item["name"]
        if name in seen:
            continue
        seen.add(name)
        std = standards.get(name, {"default": None, "friday": None, "event": None})
        products.append({
            "name":     name,
            "location": item["location"],
            "note":     item["note"],
            "rare":     item["rare"],
            "standards": std,
            "active":   True,
        })

    # 定数表にのみある商品も追加（場所不明として）
    for name, std in standards.items():
        if name in seen:
            continue
        seen.add(name)
        products.append({
            "name":     name,
            "location": "場所未設定",
            "note":     "",
            "rare":     False,
            "standards": std,
            "active":   True,
        })

    return products

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    print("📦 商品データ取り込み開始...")

    standards   = load_standards()
    stock_items = load_stock_sheet()
    products    = build_products(standards, stock_items)

    out_path = os.path.join(DATA_DIR, "products.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"products": products}, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完了！ {len(products)}件 → {out_path}")
    print("\n保管場所の内訳:")
    from collections import Counter
    locs = Counter(p["location"] for p in products)
    for loc, cnt in sorted(locs.items(), key=lambda x: -x[1]):
        print(f"  {loc}: {cnt}件")

if __name__ == "__main__":
    main()
