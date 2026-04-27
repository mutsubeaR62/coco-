import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from utils import apply_theme, require_login, page_header, load_json, save_json, get_progress, save_progress, award_stamps, show_new_stamps

apply_theme()
require_login()

user = st.session_state.user
if user.get("role") == "kenshu":
    st.error("🚫 発注管理は研修中のメンバーはアクセスできません。")
    st.stop()
username = user["username"]
role     = user.get("role", "new")

# ─── 商品データ読み込み ──────────────────────────────────────
def get_products():
    data = load_json("products.json", {"products": []})
    return [p for p in data.get("products", []) if p.get("active", True)]

def save_products_data(products):
    save_json("products.json", {"products": products})

# ─── バックアップ ─────────────────────────────────────────────
def backup_stock(stock_state, label="手動"):
    history = load_json("stock_backup.json", {"backups": []})
    history["backups"].insert(0, {
        "id":    datetime.now().strftime("%Y%m%d_%H%M%S"),
        "label": label,
        "user":  user["name"],
        "stock": dict(stock_state),
    })
    history["backups"] = history["backups"][:30]  # 直近30件
    save_json("stock_backup.json", history)

def get_backups():
    return load_json("stock_backup.json", {"backups": []}).get("backups", [])

# ─── 発注数計算 ───────────────────────────────────────────────
def calc_order(std, stock, next_delivery=0):
    """
    std          : 定数（その曜日の基準在庫）
    stock        : 現在庫
    next_delivery: 翌日納品数（金曜発注時は木曜発注分を加算）
    → 金曜発注 = 金曜定数 - (在庫数 + 木曜翌納数)
    """
    if std is None:
        return None
    effective = stock + next_delivery
    return max(0, std - effective)

# ─── セッション初期化 ─────────────────────────────────────────
def init_session(products):
    if "stock_state" not in st.session_state:
        st.session_state.stock_state = {p["name"]: 0 for p in products}
    # 新商品が追加されたときに備えて補完
    for p in products:
        if p["name"] not in st.session_state.stock_state:
            st.session_state.stock_state[p["name"]] = 0

# ─── ページ本体 ──────────────────────────────────────────────
page_header("📦 発注管理", "在庫数を入力して発注数を確認しよう")

products = get_products()
if not products:
    st.warning("商品データがありません。")
    st.info("👇 まずこのコマンドを実行して商品データを取り込んでください：\n```\npython import_products.py\n```")
    st.stop()

init_session(products)

tab_order, tab_next, tab_history, tab_manage = st.tabs(
    ["📝 在庫入力・発注", "📬 翌日納品", "📜 発注履歴", "⚙️ 商品管理"]
)

# ════ TAB1: 在庫入力・発注 ════════════════════════════════════
with tab_order:
    # ─ 上部コントロール ─
    col_day, col_loc, col_search = st.columns([2, 2, 3])

    # 曜日を自動判断してデフォルト選択
    weekday = datetime.now().weekday()  # 0=月 … 6=日
    auto_day = "金曜日" if weekday == 4 else "通常（月〜木）"
    day_options = ["通常（月〜木）", "金曜日", "イベント発注"]
    auto_index  = day_options.index(auto_day)

    with col_day:
        day_type = st.selectbox(
            "📅 曜日・発注種別",
            day_options,
            index=auto_index,
            help="今日の曜日に合わせて自動で切り替わります。手動でも変更できます。"
        )
        weekday_labels = ["月", "火", "水", "木", "金", "土", "日"]
        st.caption(f"📅 今日は{weekday_labels[weekday]}曜日（自動判定）")
    day_key = {"通常（月〜木）": "default", "金曜日": "friday", "イベント発注": "event"}[day_type]

    # 保管場所一覧 ─ CSVの順番を保持（ソートしない）
    seen_locs = {}
    for p in products:
        loc = p.get("location", "")
        if loc and loc not in seen_locs:
            seen_locs[loc] = True
    locations = list(seen_locs.keys())

    with col_loc:
        sel_loc = st.selectbox("🏪 保管場所で絞り込み", ["すべて"] + locations)

    with col_search:
        search = st.text_input("🔍 商品名で検索", placeholder="例: ロースカツ")

    # 一括クリア・バックアップ
    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("💾 在庫をバックアップ", use_container_width=True):
            backup_stock(st.session_state.stock_state)
            st.success("バックアップしました！")
    with col_b2:
        if st.button("🔄 在庫を全クリア", use_container_width=True):
            backup_stock(st.session_state.stock_state, label="クリア前自動バックアップ")
            st.session_state.stock_state = {p["name"]: 0 for p in products}
            st.rerun()
    with col_b3:
        backups = get_backups()
        if backups and st.button(f"↩️ 最新バックアップに戻す", use_container_width=True):
            latest = backups[0]
            for name, val in latest["stock"].items():
                if name in st.session_state.stock_state:
                    st.session_state.stock_state[name] = val
            st.success(f"復元: {latest['id']} ({latest['user']})")
            st.rerun()

    # 金曜発注時：木曜翌納数を読み込む
    next_delivery_data = {}
    if day_key == "friday":
        nd = load_json("next_delivery.json", {"items": {}}).get("items", {})
        next_delivery_data = {name: v.get("normal", 0) for name, v in nd.items()}
        st.info("📬 **金曜発注モード** — 発注数 ＝ 金曜定数 − (現在庫 ＋ 木曜翌納数)　※「翌日納品」タブで木曜翌納数を先に入力してください。")

    # ─ 凡例 ─
    st.markdown("""
<div style='display:flex; gap:16px; flex-wrap:wrap; margin:8px 0 4px; align-items:center;'>
  <span style='font-weight:600; color:#555; font-size:0.85rem;'>色の見方：</span>
  <span style='background:#fff3e0; border:2px solid #e85d04; border-radius:6px;
               padding:2px 10px; font-weight:700; color:#e85d04; font-size:0.85rem;'>
    ■ 数字 → 発注サイトに入力する数
  </span>
  <span style='background:#f0faf0; border:1px solid #28a745; border-radius:6px;
               padding:2px 10px; color:#28a745; font-size:0.85rem; font-weight:600;'>
    ✓ 緑 → 発注不要（在庫OK）
  </span>
  <span style='color:#aaa; font-size:0.85rem;'>— → 定数なし</span>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ─ ヘッダー行 ─
    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([4, 2, 2, 2, 3])
    with hcol1: st.caption("商品名")
    with hcol2: st.caption("現在庫")
    with hcol3: st.caption("定数")
    if day_key == "friday":
        with hcol4: st.caption("木曜翌納")
    else:
        with hcol4: st.caption("　")
    with hcol5:
        st.markdown("<span style='color:#e85d04; font-weight:700; font-size:0.9rem;'>👉 発注サイト入力数</span>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:2px 0 8px; border-color:#e85d04; border-width:2px;'>", unsafe_allow_html=True)

    # ─ 商品フィルタリング ─
    filtered = [
        p for p in products
        if (sel_loc == "すべて" or p["location"] == sel_loc)
        and search.lower() in p["name"].lower()
    ]

    if not filtered:
        st.info("条件に一致する商品がありません。")
    else:
        # 発注必要な商品カウント
        need_order = []
        for p in filtered:
            stock    = st.session_state.stock_state.get(p["name"], 0)
            std      = p.get("standards", {}).get(day_key)
            next_del = next_delivery_data.get(p["name"], 0) if day_key == "friday" else 0
            qty      = calc_order(std, stock, next_del)
            if qty and qty > 0:
                need_order.append((p, qty))

        if need_order:
            st.markdown(f"**⚠️ 発注が必要な商品: {len(need_order)}件**")
        else:
            st.success("✅ 発注が必要な商品はありません")

        # ─ 商品ごとに表示 ─
        for p in filtered:
            name     = p["name"]
            note     = p.get("note", "")
            rare     = p.get("rare", False)
            std      = p.get("standards", {}).get(day_key)
            stock    = st.session_state.stock_state.get(name, 0)
            next_del = next_delivery_data.get(name, 0) if day_key == "friday" else 0
            order    = calc_order(std, stock, next_del)

            with st.container():
                col_name, col_input, col_std, col_next, col_order = st.columns([4, 2, 2, 2, 3])

                with col_name:
                    badge = "🌟 " if rare else ""
                    st.markdown(f"**{badge}{name}**")
                    if note:
                        st.caption(f"📌 {note[:55]}{'…' if len(note) > 55 else ''}")

                with col_input:
                    new_stock = st.number_input(
                        "在庫", min_value=0, value=stock, step=1,
                        key=f"stock_{name}", label_visibility="collapsed"
                    )
                    if new_stock != stock:
                        st.session_state.stock_state[name] = new_stock
                        st.rerun()

                with col_std:
                    val = str(std) if std is not None else "—"
                    st.markdown(f"<div style='padding-top:6px; color:#555;'>{val}</div>", unsafe_allow_html=True)

                with col_next:
                    if day_key == "friday":
                        nd_val = next_del
                        color = "#2d6a4f" if nd_val > 0 else "#aaa"
                        st.markdown(f"<div style='padding-top:6px; color:{color}; font-weight:600;'>+{nd_val}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown("<div style='padding-top:6px; color:#ddd;'>—</div>", unsafe_allow_html=True)

                with col_order:
                    if order is None:
                        st.markdown("<div style='color:#ccc; padding-top:6px; text-align:center;'>—</div>", unsafe_allow_html=True)
                    elif order > 0:
                        st.markdown(f"""
<div style='background:#fff3e0; border:2px solid #e85d04; border-radius:8px;
            padding:4px 12px; font-size:1.4rem; font-weight:900;
            color:#e85d04; text-align:center; letter-spacing:1px;'>
  {order}
</div>""", unsafe_allow_html=True)
                    else:
                        st.markdown("""
<div style='background:#f0faf0; border:1px solid #28a745; border-radius:8px;
            padding:6px 12px; color:#28a745; text-align:center; font-size:1.1rem;'>
  ✓
</div>""", unsafe_allow_html=True)

                st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

                st.markdown("<hr style='margin:4px 0; border-color:#f0f0f0;'>", unsafe_allow_html=True)

    # ─ 発注サマリー＆確定 ─
    st.divider()
    order_items = []
    for p in products:
        stock    = st.session_state.stock_state.get(p["name"], 0)
        std      = p.get("standards", {}).get(day_key)
        next_del = next_delivery_data.get(p["name"], 0) if day_key == "friday" else 0
        qty      = calc_order(std, stock, next_del)
        if qty and qty > 0:
            order_items.append({"name": p["name"], "stock": stock, "next_delivery": next_del, "standard": std, "order": qty})

    if order_items:
        st.markdown("### 📋 発注サマリー")
        st.markdown('<div class="info-card">', unsafe_allow_html=True)
        cols_s = st.columns(3)
        for i, item in enumerate(order_items):
            with cols_s[i % 3]:
                st.markdown(f"• **{item['name']}**: {item['order']}個")
        st.markdown('</div>', unsafe_allow_html=True)
        st.caption(f"発注種別: {day_type} | 合計 {len(order_items)}品目")

        if st.button("📤 発注を確定・記録する", type="primary", use_container_width=True):
            record = {
                "date":     datetime.now().strftime("%Y-%m-%d %H:%M"),
                "user":     user["name"],
                "username": username,
                "day_type": day_type,
                "items":    order_items,
            }
            history = load_json("order_history.json", {"orders": []})
            history["orders"].insert(0, record)
            history["orders"] = history["orders"][:100]
            save_json("order_history.json", history)
            backup_stock(st.session_state.stock_state, label=f"発注確定({day_type})")

            # ── 翌日納品数を自動保存 ──────────────────────────────
            # 通常発注 → 翌納の「通常」列に自動反映（木曜発注 → 金曜に届く分）
            # イベント発注 → 翌納の「イベント」列に自動反映
            if day_key in ("default", "event"):
                nd_data = load_json("next_delivery.json", {"items": {}})
                nd_items = nd_data.get("items", {})
                nd_col   = "normal" if day_key == "default" else "event"
                for item in order_items:
                    name = item["name"]
                    if name not in nd_items:
                        nd_items[name] = {"normal": 0, "event": 0}
                    nd_items[name][nd_col] = item["order"]
                save_json("next_delivery.json", {
                    "items":      nd_items,
                    "updated":    datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "updated_by": user["name"],
                })
                nd_label = "通常" if day_key == "default" else "イベント"
                st.info(f"📬 翌日納品数（{nd_label}）を自動で更新しました！")

            # スタンプ進捗
            prog = get_progress(username)
            prog["order_count"] = prog.get("order_count", 0) + 1
            save_progress(username, prog)
            _, new_stamps = award_stamps(username)
            show_new_stamps(new_stamps)
            st.success("✅ 発注を記録しました！")
            st.rerun()
    else:
        st.info("発注が必要な商品はありません。")

# ════ TAB2: 翌日納品数 ════════════════════════════════════════
with tab_next:
    st.markdown("#### 📬 翌日納品数入力")
    st.caption("翌日入荷予定の数量を記録しておこう（通常・イベント別）")

    next_data = load_json("next_delivery.json", {"items": {}})
    items_nd  = next_data.get("items", {})

    col_nd1, col_nd2 = st.columns(2)
    with col_nd1:
        st.markdown("**通常翌納**")
    with col_nd2:
        st.markdown("**イベント翌納**")

    changed = False
    for p in products:
        name = p["name"]
        std  = p.get("standards", {})
        if std.get("default") is None:
            continue  # 定数なし商品はスキップ

        col1, col2, col3 = st.columns([4, 2, 2])
        with col1:
            st.write(name)
        with col2:
            v_normal = st.number_input(
                "通常", min_value=0,
                value=int(items_nd.get(name, {}).get("normal", 0)),
                key=f"nd_n_{name}", label_visibility="collapsed"
            )
        with col3:
            v_event = st.number_input(
                "イベント", min_value=0,
                value=int(items_nd.get(name, {}).get("event", 0)),
                key=f"nd_e_{name}", label_visibility="collapsed"
            )
        if name not in items_nd:
            items_nd[name] = {}
        items_nd[name]["normal"] = v_normal
        items_nd[name]["event"]  = v_event

    if st.button("💾 翌日納品数を保存", type="primary"):
        save_json("next_delivery.json", {"items": items_nd, "updated": datetime.now().strftime("%Y-%m-%d %H:%M"), "updated_by": user["name"]})
        st.success("保存しました！")

# ════ TAB3: 発注履歴 ══════════════════════════════════════════
with tab_history:
    history = load_json("order_history.json", {"orders": []}).get("orders", [])
    if not history:
        st.info("発注履歴はまだありません。")
    else:
        for rec in history[:30]:
            total = len(rec.get("items", []))
            with st.expander(f"📅 {rec['date']} — {rec['user']} ({rec.get('day_type','')}) {total}品目"):
                cols_h = st.columns(3)
                for i, item in enumerate(rec.get("items", [])):
                    with cols_h[i % 3]:
                        st.write(f"• **{item['name']}**: 在庫{item['stock']} → 発注{item['order']}")

# ════ TAB4: 商品管理（管理者のみ） ════════════════════════════
with tab_manage:
    if role != "admin":
        st.info("🔒 商品管理は管理者のみ操作できます。")
        st.stop()

    st.markdown("#### 商品一覧・編集")
    st.caption("商品の定数・場所・メモを変更できます")

    all_products = load_json("products.json", {"products": []}).get("products", [])

    # 絞り込み
    loc_filter = st.selectbox("場所で絞り込み", ["すべて"] + sorted(set(p["location"] for p in all_products if p.get("location"))))

    for i, p in enumerate(all_products):
        if loc_filter != "すべて" and p.get("location") != loc_filter:
            continue
        with st.expander(f"{'🌟 ' if p.get('rare') else ''}{p['name']} ({p.get('location', '場所不明')})"):
            c1, c2, c3 = st.columns(3)
            with c1:
                new_name = st.text_input("商品名", value=p["name"], key=f"pn_{i}")
                new_loc  = st.text_input("保管場所", value=p.get("location", ""), key=f"pl_{i}")
            with c2:
                std = p.get("standards", {})
                new_default = st.number_input("定数（通常）", value=std.get("default") or 0, min_value=0, key=f"pd_{i}")
                new_friday  = st.number_input("定数（金曜）", value=std.get("friday") or 0, min_value=0, key=f"pf_{i}")
                new_event   = st.number_input("定数（イベント）", value=std.get("event") or 0, min_value=0, key=f"pe_{i}")
            with c3:
                new_note = st.text_area("数え方メモ", value=p.get("note", ""), height=80, key=f"pnote_{i}")
                new_rare = st.checkbox("希少商品", value=p.get("rare", False), key=f"pr_{i}")
                new_active = st.checkbox("有効", value=p.get("active", True), key=f"pac_{i}")

            cs, cd = st.columns(2)
            with cs:
                if st.button("💾 保存", key=f"psave_{i}", type="primary"):
                    all_products[i].update({
                        "name": new_name, "location": new_loc, "note": new_note,
                        "rare": new_rare, "active": new_active,
                        "standards": {"default": new_default, "friday": new_friday, "event": new_event}
                    })
                    save_products_data(all_products)
                    st.success("保存しました！")
                    st.rerun()

    st.divider()
    st.markdown("#### ➕ 商品を追加")
    with st.form("add_product"):
        c1, c2 = st.columns(2)
        with c1:
            a_name  = st.text_input("商品名")
            a_loc   = st.text_input("保管場所")
            a_note  = st.text_input("数え方メモ")
        with c2:
            a_def   = st.number_input("定数（通常）", min_value=0, value=0)
            a_fri   = st.number_input("定数（金曜）",  min_value=0, value=0)
            a_eve   = st.number_input("定数（イベント）", min_value=0, value=0)
        if st.form_submit_button("追加する", type="primary"):
            if a_name:
                all_products.append({
                    "name": a_name, "location": a_loc, "note": a_note,
                    "rare": False, "active": True,
                    "standards": {"default": a_def, "friday": a_fri, "event": a_eve}
                })
                save_products_data(all_products)
                st.success(f"「{a_name}」を追加しました！")
                st.rerun()

    st.divider()
    st.markdown("#### 📥 CSVから再インポート")
    st.info("Googleスプレッドシートを更新したあと、CSVをダウンロードして下記を実行してください。")
    st.code("python import_products.py", language="bash")
