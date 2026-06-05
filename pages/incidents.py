import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from utils import (apply_theme, require_login, page_header, load_json, save_json,
                   store_path, is_manager)

apply_theme()
require_login()

page_header("クレーム・インシデント記録", "過去の事例を記録・検索して対応力を高める")

user   = st.session_state.user
is_mgr = is_manager(user)

CATEGORIES = ["クレーム", "食品・衛生", "接客ミス", "設備・その他"]
CAT_COLOR  = {
    "クレーム":    "#e53935",
    "食品・衛生":  "#f9a825",
    "接客ミス":    "#fb8c00",
    "設備・その他":"#757575",
}
CAT_ICON = {
    "クレーム":    "⚠️",
    "食品・衛生":  "🍽️",
    "接客ミス":    "💬",
    "設備・その他":"🔧",
}

def _load():
    return load_json(store_path("incidents.json"), {"incidents": []})

def _save(data):
    save_json(store_path("incidents.json"), data)

# ─── 検索・フィルター ──────────────────────────────────────────
col_s, col_f = st.columns([3, 1])
with col_s:
    keyword = st.text_input("キーワード検索", placeholder="例: スープ冷たい、待ち時間、異物",
                             label_visibility="collapsed")
with col_f:
    cat_filter = st.selectbox("カテゴリ", ["すべて"] + CATEGORIES, label_visibility="collapsed")

# ─── 新規登録フォーム（管理者・代行のみ） ─────────────────────
if is_mgr:
    with st.expander("新しい事例を登録する"):
        with st.form("add_incident"):
            i_title    = st.text_input("タイトル（一言まとめ）", placeholder="例: スープの温度クレーム")
            i_cat      = st.selectbox("カテゴリ", CATEGORIES)
            i_date     = st.date_input("発生日", value=datetime.now().date())
            i_situation = st.text_area("状況（何が起きたか）", height=100,
                                       placeholder="例: テイクアウトのお客様よりスープが冷たいとクレームが入った")
            i_response  = st.text_area("対応（どう対応したか）", height=100,
                                       placeholder="例: まず謝罪し、すぐに温め直して提供した。店長へも報告した")
            i_result    = st.text_area("結果・学んだこと", height=80,
                                       placeholder="例: お客様にご納得いただけた。テイクアウト時は保温バッグを必ず使う")

            if st.form_submit_button("登録する", type="primary"):
                if not i_title or not i_situation or not i_response:
                    st.error("タイトル・状況・対応は必須です。")
                else:
                    import uuid
                    data = _load()
                    data["incidents"].insert(0, {
                        "id":         str(uuid.uuid4())[:8],
                        "title":      i_title,
                        "category":   i_cat,
                        "date":       str(i_date),
                        "situation":  i_situation,
                        "response":   i_response,
                        "result":     i_result,
                        "author":     user["name"],
                        "created_at": datetime.now().isoformat(),
                    })
                    _save(data)
                    st.success(f"「{i_title}」を登録しました。")
                    st.rerun()

st.divider()

# ─── 事例一覧 ─────────────────────────────────────────────────
data      = _load()
incidents = data["incidents"]

# フィルター適用
if cat_filter != "すべて":
    incidents = [i for i in incidents if i.get("category") == cat_filter]
if keyword:
    kw = keyword.lower()
    incidents = [
        i for i in incidents
        if kw in i.get("title","").lower()
        or kw in i.get("situation","").lower()
        or kw in i.get("response","").lower()
        or kw in i.get("result","").lower()
    ]

if not incidents:
    st.info("該当する事例はありません。" if (keyword or cat_filter != "すべて") else "まだ事例が登録されていません。")
else:
    st.caption(f"{len(incidents)} 件")
    for inc in incidents:
        cat   = inc.get("category", "その他")
        color = CAT_COLOR.get(cat, "#888")
        icon  = CAT_ICON.get(cat, "📋")

        with st.expander(f"{icon} {inc['date']}　{inc['title']}　— {cat}"):
            st.markdown(
                f"<div style='display:flex;gap:8px;margin-bottom:12px;'>"
                f"<span style='background:{color};color:white;border-radius:6px;"
                f"padding:2px 10px;font-size:0.75rem;font-weight:700;'>{cat}</span>"
                f"<span style='font-size:0.75rem;color:#999;'>登録者: {inc.get('author','')} · {inc.get('date','')}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

            st.markdown("**状況**")
            st.markdown(
                f"<div style='background:#fff8f0;border-left:3px solid {color};"
                f"border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.88rem;"
                f"white-space:pre-wrap;margin-bottom:10px;'>{inc['situation']}</div>",
                unsafe_allow_html=True,
            )
            st.markdown("**対応**")
            st.markdown(
                f"<div style='background:#f0f7ff;border-left:3px solid #1e88e5;"
                f"border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.88rem;"
                f"white-space:pre-wrap;margin-bottom:10px;'>{inc['response']}</div>",
                unsafe_allow_html=True,
            )
            if inc.get("result"):
                st.markdown("**結果・学んだこと**")
                st.markdown(
                    f"<div style='background:#f1f8e9;border-left:3px solid #43a047;"
                    f"border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.88rem;"
                    f"white-space:pre-wrap;'>{inc['result']}</div>",
                    unsafe_allow_html=True,
                )

            if is_mgr:
                st.markdown("")
                if st.button("この事例を削除", key=f"del_inc_{inc['id']}", type="secondary"):
                    data["incidents"] = [x for x in data["incidents"] if x["id"] != inc["id"]]
                    _save(data)
                    st.rerun()
