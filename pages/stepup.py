import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_login, page_header,
                   get_all_users, is_manager, load_json, save_json, ROLE_LABELS)
from datetime import datetime

apply_theme()
require_login()

page_header("📈 ステップアップ表", "スキル習得の進捗を確認しよう")

user = st.session_state.user
username = user["username"]
_is_manager = is_manager(user)

# ─── データ読み込み ───────────────────────────────────────────
def get_stepup_data():
    return load_json("stepup_data.json", {"stages": []})

def save_stepup_data(data):
    save_json("stepup_data.json", data)

def get_stepup_progress(target_username):
    data = load_json("stepup_progress.json", {})
    return data.get(target_username, {})

def save_stepup_progress(target_username, progress):
    data = load_json("stepup_progress.json", {})
    data[target_username] = progress
    save_json("stepup_progress.json", data)

def count_stage_progress(stage, progress):
    total = sum(len(sec["items"]) for sec in stage.get("sections", []))
    checked = 0
    for sec in stage.get("sections", []):
        for item in sec["items"]:
            key = f"{stage['id']}::{sec['name']}::{item}"
            if progress.get(key):
                checked += 1
    return checked, total

# ─── タブ ────────────────────────────────────────────────────
if _is_manager:
    tab_view, tab_edit = st.tabs(["📋 進捗確認・チェック", "✏️ 項目編集"])
else:
    tab_view = st.container()
    tab_edit = None

# ════ 進捗確認・チェック ════════════════════════════════════════
with tab_view:
    stepup = get_stepup_data()
    stages = stepup.get("stages", [])

    # 対象ユーザー選択（管理者は全員、一般は自分のみ）
    if _is_manager:
        all_users = get_all_users()
        user_options = {f"{ROLE_LABELS.get(u.get('role',''), '')} {u['name']}": u["username"]
                        for u in all_users}
        selected_name = st.selectbox("対象メンバー", list(user_options.keys()))
        target_username = user_options[selected_name]
    else:
        target_username = username

    progress = get_stepup_progress(target_username)

    # 全体進捗バー
    all_total = sum(
        sum(len(sec["items"]) for sec in stage.get("sections", []))
        for stage in stages
    )
    all_checked = sum(
        sum(1 for sec in stage.get("sections", [])
            for item in sec["items"]
            if progress.get(f"{stage['id']}::{sec['name']}::{item}"))
        for stage in stages
    )
    if all_total > 0:
        pct = int(all_checked / all_total * 100)
        st.markdown(f"""
<div style='background:white;border-radius:12px;padding:14px 20px;
            box-shadow:0 2px 10px rgba(0,0,0,0.07);margin-bottom:16px;'>
  <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
    <span style='font-weight:700;'>総合進捗</span>
    <span style='color:#e85d04;font-weight:700;'>{all_checked}/{all_total}項目 ({pct}%)</span>
  </div>
  <div style='background:#f0f0f0;border-radius:99px;height:12px;'>
    <div style='background:linear-gradient(90deg,#e85d04,#f48c06);
                width:{pct}%;height:12px;border-radius:99px;
                transition:width 0.4s;'></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ─── ステージ一覧 ─────────────────────────────────────────
    for stage in stages:
        checked, total = count_stage_progress(stage, progress)
        stage_pct = int(checked / total * 100) if total > 0 else 0
        color = stage.get("color", "#e85d04")
        completed = checked == total and total > 0

        badge = "✅ " if completed else ""
        with st.expander(
            f"{badge}{stage['title']}　{stage.get('target', '')}　{checked}/{total}項目",
            expanded=(not completed)
        ):
            # ステージ内進捗バー
            st.markdown(f"""
<div style='background:#f8f9fa;border-radius:8px;padding:8px 12px;margin-bottom:12px;'>
  <div style='display:flex;justify-content:space-between;font-size:0.85rem;margin-bottom:4px;'>
    <span style='color:{color};font-weight:700;'>{stage['title']}</span>
    <span style='color:#666;'>{checked}/{total}項目 ({stage_pct}%)</span>
  </div>
  <div style='background:#e0e0e0;border-radius:99px;height:8px;'>
    <div style='background:{color};width:{stage_pct}%;height:8px;border-radius:99px;'></div>
  </div>
</div>
""", unsafe_allow_html=True)

            # セクション別チェックリスト
            updated = False
            for sec in stage.get("sections", []):
                st.markdown(f"**{sec['name']}**")
                for item in sec["items"]:
                    key = f"{stage['id']}::{sec['name']}::{item}"
                    current = progress.get(key, False)
                    if _is_manager:
                        new_val = st.checkbox(item, value=current,
                                              key=f"chk_{target_username}_{key}")
                        if new_val != current:
                            progress[key] = new_val
                            updated = True
                    else:
                        icon = "✅" if current else "⬜"
                        st.markdown(f"{icon} {item}")

            if updated and _is_manager:
                progress["_updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                progress["_updated_by"] = user["name"]
                save_stepup_progress(target_username, progress)
                st.success("保存しました！")
                st.rerun()

# ════ 項目編集（管理者のみ） ══════════════════════════════════
if _is_manager and tab_edit is not None:
    with tab_edit:
        st.markdown("#### ✏️ ステップアップ項目の編集")
        st.caption("各ステージ・セクションの項目を追加・削除・編集できます。")

        stepup = get_stepup_data()
        stages = stepup.get("stages", [])

        for s_idx, stage in enumerate(stages):
            with st.expander(f"📌 {stage['title']}"):
                col1, col2 = st.columns(2)
                with col1:
                    new_title = st.text_input("ステージ名", value=stage["title"],
                                              key=f"stitle_{s_idx}")
                with col2:
                    new_target = st.text_input("達成目安", value=stage.get("target", ""),
                                               key=f"starget_{s_idx}")

                for sec_idx, sec in enumerate(stage.get("sections", [])):
                    st.markdown(f"**セクション: {sec['name']}**")
                    new_sec_name = st.text_input("セクション名", value=sec["name"],
                                                  key=f"secname_{s_idx}_{sec_idx}")

                    # 既存項目の編集
                    new_items = []
                    for i_idx, item in enumerate(sec["items"]):
                        col_item, col_del = st.columns([9, 1])
                        with col_item:
                            new_item = st.text_input("", value=item,
                                                      key=f"item_{s_idx}_{sec_idx}_{i_idx}",
                                                      label_visibility="collapsed")
                        with col_del:
                            delete = st.button("🗑️", key=f"del_{s_idx}_{sec_idx}_{i_idx}",
                                               help="削除")
                        if not delete:
                            new_items.append(new_item)

                    # 新規項目追加
                    new_add = st.text_input("➕ 項目を追加",
                                             placeholder="新しい項目を入力してEnter",
                                             key=f"add_{s_idx}_{sec_idx}")
                    if new_add:
                        new_items.append(new_add)

                    stages[s_idx]["sections"][sec_idx]["name"] = new_sec_name
                    stages[s_idx]["sections"][sec_idx]["items"] = new_items

                stages[s_idx]["title"] = new_title
                stages[s_idx]["target"] = new_target

                # セクション追加
                new_sec = st.text_input("➕ セクションを追加",
                                         placeholder="新しいセクション名",
                                         key=f"addsec_{s_idx}")
                if new_sec:
                    stages[s_idx]["sections"].append({"name": new_sec, "items": []})

                if st.button("💾 このステージを保存", key=f"save_stage_{s_idx}",
                             type="primary"):
                    save_stepup_data({"stages": stages})
                    st.success("保存しました！")
                    st.rerun()

        st.divider()
        st.markdown("#### ➕ 新しいステージを追加")
        with st.form("add_stage"):
            ns_title  = st.text_input("ステージ名")
            ns_target = st.text_input("達成目安（任意）", placeholder="例: 達成目安　○○時間")
            ns_color  = st.color_picker("カラー", value="#e85d04")
            if st.form_submit_button("追加する", type="primary"):
                if ns_title:
                    new_id = ns_title.replace(" ", "_").lower()
                    stages.append({
                        "id": new_id,
                        "title": ns_title,
                        "subtitle": "",
                        "target": ns_target,
                        "color": ns_color,
                        "sections": []
                    })
                    save_stepup_data({"stages": stages})
                    st.success(f"「{ns_title}」を追加しました！")
                    st.rerun()
