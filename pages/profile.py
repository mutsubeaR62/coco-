import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from utils import (apply_theme, require_login, page_header,
                   get_all_users, update_user, get_coco_spec, coco_spec_badge,
                   SERVICE_LEVELS, COOKING_LEVELS, ROLE_LABELS, get_employee_type,
                   load_json, SECRET_QUESTIONS)

apply_theme()
require_login()

page_header("👤 マイプロフィール", "自分の情報を確認・更新できます")

user = st.session_state.user
username = user["username"]
is_admin = user.get("role") == "admin"

# 最新のユーザー情報を取得
all_users = get_all_users()
me = next((u for u in all_users if u["username"] == username), user)

# ─── CoCoスペ表示 ──────────────────────────────────────────────
spec = get_coco_spec(me)

st.markdown("### 🏅 CoCoスペ")
st.markdown(
    "<div style='background:white;border-radius:12px;padding:16px 20px;"
    "box-shadow:0 2px 10px rgba(0,0,0,0.08);margin-bottom:16px;'>"
    + coco_spec_badge(spec) +
    "</div>",
    unsafe_allow_html=True,
)

# 詳細カード
c1, c2 = st.columns(2)
with c1:
    svc = spec.get("service") or "未取得"
    color = "#e85d04" if svc == "スター" else ("#5b4b97" if svc != "未取得" else "#999")
    st.markdown(
        f"<div style='background:white;border-radius:12px;padding:16px;text-align:center;"
        f"box-shadow:0 2px 8px rgba(0,0,0,0.07);border-top:4px solid {color};'>"
        f"<div style='font-size:0.8rem;color:#666;'>接客レベル</div>"
        f"<div style='font-size:1.8rem;font-weight:700;color:{color};margin-top:4px;'>{svc}</div>"
        f"<div style='font-size:0.75rem;color:#aaa;margin-top:4px;'>3級 → 2級 → 1級 → スター</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with c2:
    ckng = spec.get("cooking") or "未取得"
    color2 = "#1e6ab5" if ckng != "未取得" else "#999"
    st.markdown(
        f"<div style='background:white;border-radius:12px;padding:16px;text-align:center;"
        f"box-shadow:0 2px 8px rgba(0,0,0,0.07);border-top:4px solid {color2};'>"
        f"<div style='font-size:0.8rem;color:#666;'>調理レベル</div>"
        f"<div style='font-size:1.8rem;font-weight:700;color:{color2};margin-top:4px;'>{ckng}</div>"
        f"<div style='font-size:0.75rem;color:#aaa;margin-top:4px;'>3級 → 2級 → 1級</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

if is_admin:
    st.caption("CoCoスペは管理者ページから変更できます。")
else:
    st.caption("CoCoスペの変更は管理者にお申し付けください。")

st.divider()

# ─── プロフィール編集 ──────────────────────────────────────────
st.markdown("### ✏️ プロフィール編集")

with st.form("edit_profile"):
    st.markdown("**基本情報**")
    col_a, col_b = st.columns(2)
    with col_a:
        new_name = st.text_input("表示名", value=me.get("name", ""))
        role_label = ROLE_LABELS.get(me.get("role", ""), "")
        st.text_input("権限", value=role_label, disabled=True)
    with col_b:
        emp_label = "バイト" if get_employee_type(me) == "baito" else "社員"
        st.text_input("雇用形態", value=emp_label, disabled=True)
        # 誕生日: YYYY-MM-DD または MM-DD 形式で保存
        bd_val = me.get("birthday", "") or ""
        new_birthday = st.text_input("誕生日", value=bd_val,
                                      placeholder="例: 07-15 または 2002-07-15",
                                      help="月-日（MM-DD）または 年-月-日（YYYY-MM-DD）で入力")

    st.markdown("**CoCoスペ**（管理者のみ変更可能）")
    col_c, col_d = st.columns(2)
    with col_c:
        svc_opts = [x if x else "未取得" for x in SERVICE_LEVELS]
        cur_svc = spec.get("service") or "未取得"
        new_svc_label = st.selectbox("接客レベル", svc_opts,
                                      index=svc_opts.index(cur_svc) if cur_svc in svc_opts else 0,
                                      disabled=not is_admin)
    with col_d:
        ckng_opts = [x if x else "未取得" for x in COOKING_LEVELS]
        cur_ckng = spec.get("cooking") or "未取得"
        new_ckng_label = st.selectbox("調理レベル", ckng_opts,
                                       index=ckng_opts.index(cur_ckng) if cur_ckng in ckng_opts else 0,
                                       disabled=not is_admin)

    st.divider()
    st.markdown("**秘密の質問（パスワードリセット用）**")
    cur_q = me.get("secret_question", "") or ""
    sq_opts = SECRET_QUESTIONS
    sq_idx = sq_opts.index(cur_q) if cur_q in sq_opts else 0
    new_sq = st.selectbox("質問", sq_opts, index=sq_idx)
    new_sa = st.text_input("新しい答え（変更しない場合は空欄）",
                            type="password", placeholder="変更する場合のみ入力")

    if st.form_submit_button("💾 保存", type="primary"):
        kwargs = {"name": new_name, "birthday": new_birthday,
                  "secret_question": new_sq}
        if new_sa:
            kwargs["secret_answer"] = new_sa
        if is_admin:
            kwargs["coco_spec"] = {
                "service": None if new_svc_label == "未取得" else new_svc_label,
                "cooking": None if new_ckng_label == "未取得" else new_ckng_label,
            }
        update_user(username, **kwargs)
        st.session_state.user["name"] = new_name
        st.success("✅ プロフィールを更新しました！")
        st.rerun()

st.divider()

# ─── 他メンバーのCoCoスペ一覧（管理者のみ） ─────────────────────
if is_admin:
    st.markdown("### 📋 全メンバーのCoCoスペ一覧")

    rows = []
    for u in all_users:
        sp = get_coco_spec(u)
        rows.append({
            "名前": u.get("name", ""),
            "接客": sp.get("service") or "—",
            "調理": sp.get("cooking") or "—",
            "雇用形態": "バイト" if get_employee_type(u) == "baito" else "社員",
        })

    import pandas as pd
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown("#### ✏️ メンバーのCoCoスペを更新")
    user_opts = {u["name"]: u["username"] for u in all_users}
    target_name = st.selectbox("対象メンバー", list(user_opts.keys()), key="spec_target")
    target_uname = user_opts[target_name]
    target_user = next((u for u in all_users if u["username"] == target_uname), {})
    tspec = get_coco_spec(target_user)

    col_e, col_f = st.columns(2)
    svc_opts2 = [x if x else "未取得" for x in SERVICE_LEVELS]
    cur_svc2 = tspec.get("service") or "未取得"
    new_svc2 = col_e.selectbox("接客レベル", svc_opts2,
                                index=svc_opts2.index(cur_svc2) if cur_svc2 in svc_opts2 else 0,
                                key="svc2")
    ckng_opts2 = [x if x else "未取得" for x in COOKING_LEVELS]
    cur_ckng2 = tspec.get("cooking") or "未取得"
    new_ckng2 = col_f.selectbox("調理レベル", ckng_opts2,
                                 index=ckng_opts2.index(cur_ckng2) if cur_ckng2 in ckng_opts2 else 0,
                                 key="ckng2")

    if st.button("CoCoスペを更新", type="primary", key="upd_spec"):
        update_user(target_uname, coco_spec={
            "service": None if new_svc2 == "未取得" else new_svc2,
            "cooking": None if new_ckng2 == "未取得" else new_ckng2,
        })
        st.success(f"✅ {target_name}さんのCoCoスペを更新しました。")
        st.rerun()
