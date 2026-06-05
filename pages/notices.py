import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from utils import (apply_theme, require_login, page_header, load_json, save_json,
                   store_path, get_all_users, is_manager, get_shift_schedule)

apply_theme()
require_login()

page_header("お知らせ", "スタッフへの連絡・伝言板")

user     = st.session_state.user
username = user["username"]
is_mgr   = is_manager(user)

CATEGORIES = ["お知らせ", "シフト変更", "お願い", "緊急"]
CAT_COLOR  = {
    "お知らせ": "#1e88e5",
    "シフト変更": "#f9a825",
    "お願い": "#43a047",
    "緊急": "#e53935",
}

def _load():
    return load_json(store_path("notices.json"), {"notices": []})

def _save(data):
    save_json(store_path("notices.json"), data)

def _mark_read(notice_id):
    data = _load()
    for n in data["notices"]:
        if n["id"] == notice_id:
            reads = set(n.get("reads", []))
            reads.add(username)
            n["reads"] = list(reads)
            break
    _save(data)

def _unread_count():
    today = datetime.now().strftime("%Y-%m-%d")
    notices = _load()["notices"]
    count = 0
    for n in notices:
        if username not in n.get("reads", []):
            # 対象チェック
            target = n.get("target", "all")
            if target == "all":
                count += 1
            elif target.startswith("shift:"):
                date = target.split(":", 1)[1]
                if date == today:
                    sched = get_shift_schedule(date)
                    if username in sched.get("members", []):
                        count += 1
            elif isinstance(target, list) and username in target:
                count += 1
    return count

# ─── 投稿フォーム（管理者・代行のみ） ────────────────────────
if is_mgr:
    with st.expander("投稿する", expanded=False):
        with st.form("post_notice"):
            n_title = st.text_input("タイトル", placeholder="例: 今週のシフト変更について")
            n_body  = st.text_area("内容", height=120, placeholder="伝えたいことを書いてください")
            c1, c2 = st.columns(2)
            with c1:
                n_cat = st.selectbox("カテゴリ", CATEGORIES)
            with c2:
                n_target_label = st.selectbox(
                    "対象",
                    ["全員", "今日のシフトメンバー", "特定のメンバー"]
                )
            n_target_members = []
            if n_target_label == "特定のメンバー":
                all_users = get_all_users()
                opts = {u["name"]: u["username"] for u in all_users if u["username"] != username}
                selected_names = st.multiselect("メンバーを選ぶ", list(opts.keys()))
                n_target_members = [opts[n] for n in selected_names]

            if st.form_submit_button("投稿する", type="primary"):
                if not n_title or not n_body:
                    st.error("タイトルと内容を入力してください。")
                else:
                    import uuid
                    if n_target_label == "全員":
                        target = "all"
                    elif n_target_label == "今日のシフトメンバー":
                        target = f"shift:{datetime.now().strftime('%Y-%m-%d')}"
                    else:
                        target = n_target_members or "all"

                    data = _load()
                    data["notices"].insert(0, {
                        "id":         str(uuid.uuid4())[:8],
                        "title":      n_title,
                        "body":       n_body,
                        "category":   n_cat,
                        "target":     target,
                        "author":     user["name"],
                        "created_at": datetime.now().isoformat(),
                        "reads":      [username],
                    })
                    # 古い投稿は100件まで保持
                    data["notices"] = data["notices"][:100]
                    _save(data)
                    st.success("投稿しました！")
                    st.rerun()

st.divider()

# ─── お知らせ一覧 ─────────────────────────────────────────────
data    = _load()
notices = data["notices"]
today   = datetime.now().strftime("%Y-%m-%d")

# 自分に関係するものだけフィルター
def _is_for_me(n):
    target = n.get("target", "all")
    if target == "all":
        return True
    if isinstance(target, list):
        return username in target
    if isinstance(target, str) and target.startswith("shift:"):
        date = target.split(":", 1)[1]
        sched = get_shift_schedule(date)
        return username in sched.get("members", [])
    return True

visible = [n for n in notices if _is_for_me(n)]

if not visible:
    st.info("現在お知らせはありません。")
else:
    for n in visible:
        is_read  = username in n.get("reads", [])
        cat      = n.get("category", "お知らせ")
        color    = CAT_COLOR.get(cat, "#888")
        dt_str   = n.get("created_at", "")[:16].replace("T", " ")
        target   = n.get("target", "all")

        if target == "all":
            target_label = "全員"
        elif isinstance(target, str) and target.startswith("shift:"):
            target_label = f"{target.split(':')[1]} シフトメンバー"
        else:
            target_label = "指定メンバー"

        # 未読は強調
        bg    = "white" if is_read else "#fff8f0"
        border = "#ddd" if is_read else color
        opacity = "0.7" if is_read else "1"

        st.markdown(
            f"<div style='background:{bg};border:1.5px solid {border};border-radius:12px;"
            f"padding:14px 18px;margin-bottom:10px;opacity:{opacity};'>"
            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
            f"<span style='background:{color};color:white;border-radius:6px;"
            f"padding:2px 10px;font-size:0.72rem;font-weight:700;'>{cat}</span>"
            f"<span style='font-size:0.72rem;color:#999;'>{target_label} · {dt_str} · {n.get('author','')}</span>"
            f"{'<span style=\"background:#e85d04;color:white;border-radius:6px;padding:1px 8px;font-size:0.68rem;margin-left:auto;\">未読</span>' if not is_read else ''}"
            f"</div>"
            f"<div style='font-weight:700;font-size:1rem;margin-bottom:4px;'>{n['title']}</div>"
            f"<div style='font-size:0.88rem;color:#444;white-space:pre-wrap;'>{n['body']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        col_read, col_del = st.columns([3, 1])
        with col_read:
            if not is_read:
                if st.button("既読にする", key=f"read_{n['id']}", use_container_width=True):
                    _mark_read(n["id"])
                    st.rerun()
        with col_del:
            if is_mgr:
                if st.button("削除", key=f"del_{n['id']}", use_container_width=True):
                    data["notices"] = [x for x in data["notices"] if x["id"] != n["id"]]
                    _save(data)
                    st.rerun()
