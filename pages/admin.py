import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_admin, page_header,
                   get_all_users, add_user, delete_user, update_user,
                   get_progress, STAMPS, ROLE_LABELS, get_employee_type,
                   get_coco_spec, coco_spec_badge, SERVICE_LEVELS, COOKING_LEVELS)

apply_theme()
require_admin()

page_header("⚙️ 管理者設定", "メンバー管理・進捗確認")

tab_members, tab_progress, tab_pw = st.tabs(["👥 メンバー管理", "📊 進捗確認", "🔑 パスワード変更"])

# ════ メンバー管理 ══════════════════════════════════════════════
with tab_members:
    users = get_all_users()
    current_username = st.session_state.user["username"]

    # 統計
    counts = {}
    for u in users:
        r = u.get("role", "new")
        counts[r] = counts.get(r, 0) + 1

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("👑 管理者", counts.get("admin", 0))
    with c2:
        st.metric("🏪 スタッフ", counts.get("staff", 0))
    with c3:
        st.metric("🌱 新人", counts.get("new", 0))
    with c4:
        st.metric("合計", len(users))

    st.divider()

    # メンバー一覧
    st.markdown("#### メンバー一覧")
    for u in users:
        role_label = ROLE_LABELS.get(u.get("role", "new"), "")
        is_self = u["username"] == current_username
        with st.expander(f"{role_label} {u['name']} (@{u['username']}) {'— 自分' if is_self else ''}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**参加日:** {u.get('joined', '不明')}")
                st.write(f"**誕生日:** {u.get('birthday', '') or '未設定'}")
                prog = get_progress(u["username"])
                scores = prog.get("quiz_scores", [])
                stamp_count = len(prog.get("stamps", []))
                st.write(f"**スタンプ:** {stamp_count}/{len(STAMPS)}個")
                if scores:
                    st.write(f"**クイズ最高点:** {max(scores)}/10")
                # CoCoスペ
                spec = get_coco_spec(u)
                st.markdown("**CoCoスペ:** " + coco_spec_badge(spec), unsafe_allow_html=True)
            with col2:
                _roles = ["kenshu", "mate", "daiko", "admin"]
                _cur = u.get("role", "kenshu") if u.get("role") in _roles else "mate"
                new_role = st.selectbox(
                    "ステータス",
                    options=_roles,
                    index=_roles.index(_cur),
                    format_func=lambda x: ROLE_LABELS.get(x, x),
                    key=f"role_{u['username']}"
                )
                emp_opts = ["baito", "seishain"]
                new_emp = st.selectbox(
                    "雇用形態",
                    options=emp_opts,
                    index=emp_opts.index(get_employee_type(u)),
                    format_func=lambda x: "バイト" if x == "baito" else "社員",
                    key=f"emp_{u['username']}"
                )
                new_wage = st.number_input(
                    "時給 (¥)", value=int(u.get("hourly_wage", 1050)),
                    step=10, min_value=500, key=f"wage_{u['username']}"
                )
                new_bday = st.text_input(
                    "誕生日", value=u.get("birthday", "") or "",
                    placeholder="例: 07-15 または 2002-07-15",
                    key=f"bday_{u['username']}"
                )
                # CoCoスペ
                cur_spec = get_coco_spec(u)
                svc_opts = [x if x else "未取得" for x in SERVICE_LEVELS]
                cur_svc = cur_spec.get("service") or "未取得"
                new_svc = st.selectbox(
                    "接客レベル", svc_opts,
                    index=svc_opts.index(cur_svc) if cur_svc in svc_opts else 0,
                    key=f"svc_{u['username']}"
                )
                ckng_opts = [x if x else "未取得" for x in COOKING_LEVELS]
                cur_ckng = cur_spec.get("cooking") or "未取得"
                new_ckng = st.selectbox(
                    "調理レベル", ckng_opts,
                    index=ckng_opts.index(cur_ckng) if cur_ckng in ckng_opts else 0,
                    key=f"ckng_{u['username']}"
                )
                if st.button("更新", key=f"update_{u['username']}", type="primary"):
                    update_user(u["username"], role=new_role,
                                employee_type=new_emp, hourly_wage=new_wage,
                                birthday=new_bday,
                                coco_spec={
                                    "service": None if new_svc == "未取得" else new_svc,
                                    "cooking": None if new_ckng == "未取得" else new_ckng,
                                })
                    st.success(f"{u['name']}さんの情報を更新しました。")
                    st.rerun()
                if not is_self:
                    if st.button("🗑️ 削除", key=f"del_{u['username']}"):
                        delete_user(u["username"])
                        st.warning(f"{u['name']}さんを削除しました。")
                        st.rerun()

    st.divider()
    st.markdown("#### ➕ 新しいメンバーを追加")
    with st.form("add_member"):
        col1, col2 = st.columns(2)
        with col1:
            new_name     = st.text_input("名前（表示名）", placeholder="例: 田中太郎")
            new_username = st.text_input("ユーザー名", placeholder="例: tanaka123")
            new_pw       = st.text_input("初期パスワード", type="password", value="coco1234")
            new_bday_add = st.text_input("誕生日（任意）", placeholder="例: 07-15 または 2002-07-15")
        with col2:
            new_role = st.selectbox(
                "ステータス", options=["kenshu", "mate", "daiko", "admin"],
                format_func=lambda x: ROLE_LABELS.get(x, x)
            )
            new_emp_type = st.selectbox(
                "雇用形態", options=["baito", "seishain"],
                format_func=lambda x: "バイト" if x == "baito" else "社員"
            )
            new_wage = st.number_input("時給 (¥)", value=1050, step=10, min_value=500)
            svc_opts_add  = [x if x else "未取得" for x in SERVICE_LEVELS]
            ckng_opts_add = [x if x else "未取得" for x in COOKING_LEVELS]
            new_svc_add  = st.selectbox("接客レベル", svc_opts_add)
            new_ckng_add = st.selectbox("調理レベル", ckng_opts_add)
        if st.form_submit_button("メンバーを追加", type="primary"):
            if new_name and new_username and new_pw:
                success = add_user(new_username, new_pw, new_name, new_role,
                                   employee_type=new_emp_type, hourly_wage=new_wage)
                if success:
                    update_user(new_username,
                                birthday=new_bday_add,
                                coco_spec={
                                    "service": None if new_svc_add == "未取得" else new_svc_add,
                                    "cooking": None if new_ckng_add == "未取得" else new_ckng_add,
                                })
                    st.success(f"✅ {new_name}さん（@{new_username}）を追加しました！")
                    st.rerun()
                else:
                    st.error("そのユーザー名は既に使われています。")
            else:
                st.error("すべての項目を入力してください。")

# ════ 進捗確認 ══════════════════════════════════════════════════
with tab_progress:
    users = get_all_users()
    st.markdown("#### 全メンバーの進捗一覧")

    # 新人のみ絞り込みオプション
    show_filter = st.selectbox("表示するメンバー", ["全員", "新人のみ", "スタッフのみ", "管理者のみ"],
                               format_func=lambda x: x)
    role_filter = {"全員": None, "新人のみ": "new", "スタッフのみ": "staff", "管理者のみ": "admin"}
    filtered_role = role_filter[show_filter]

    for u in users:
        if filtered_role and u.get("role") != filtered_role:
            continue

        prog = get_progress(u["username"])
        scores = prog.get("quiz_scores", [])
        stamps = set(prog.get("stamps", []))
        cl_hist = prog.get("checklist_completions", {})
        manual_read = len(prog.get("manual_read", []))
        role_label = ROLE_LABELS.get(u.get("role", "new"), "")

        best = max(scores) if scores else 0
        cl_total = sum(cl_hist.values())

        with st.expander(f"{role_label} {u['name']} — スタンプ {len(stamps)}/{len(STAMPS)} | クイズ最高 {best}/10"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🏅 スタンプ", f"{len(stamps)}/{len(STAMPS)}")
                st.metric("🎯 クイズ最高点", f"{best}/10")
                st.metric("🔄 クイズ挑戦回数", f"{prog.get('quiz_attempts', 0)}回")
            with col2:
                st.metric("📚 マニュアル既読", f"{manual_read}セクション")
                st.metric("✅ チェックリスト完了", f"{cl_total}回")
                st.metric("📦 発注回数", f"{prog.get('order_count', 0)}回")
            with col3:
                # スタンプ表示
                st.markdown("**獲得スタンプ:**")
                for key, info in STAMPS.items():
                    if key in stamps:
                        st.write(f"{info['emoji']} {info['name']}")

            # チェックリスト詳細
            if cl_hist:
                st.markdown("**チェックリスト完了回数:**")
                for cl_name, count in cl_hist.items():
                    st.write(f"　• {cl_name}: {count}回")

            # クイズ成績グラフ
            if scores:
                import pandas as pd
                df = pd.DataFrame({"得点": scores})
                st.line_chart(df, height=120, use_container_width=True)

# ════ パスワード変更 ═════════════════════════════════════════════
with tab_pw:
    st.markdown("#### メンバーのパスワードをリセット")
    users = get_all_users()
    user_options = {u["name"]: u["username"] for u in users}

    with st.form("reset_pw"):
        target_name = st.selectbox("対象メンバー", list(user_options.keys()))
        new_pw = st.text_input("新しいパスワード", type="password")
        confirm_pw = st.text_input("確認（同じパスワードをもう一度）", type="password")
        if st.form_submit_button("パスワードを変更", type="primary"):
            if not new_pw:
                st.error("パスワードを入力してください。")
            elif new_pw != confirm_pw:
                st.error("パスワードが一致しません。")
            elif len(new_pw) < 6:
                st.error("パスワードは6文字以上にしてください。")
            else:
                target_username = user_options[target_name]
                update_user(target_username, password=new_pw)
                st.success(f"✅ {target_name}さんのパスワードを変更しました。")

    st.divider()
    st.markdown("#### 自分のパスワードを変更")
    with st.form("self_pw"):
        current_pw = st.text_input("現在のパスワード", type="password")
        s_new_pw = st.text_input("新しいパスワード", type="password")
        s_confirm_pw = st.text_input("確認", type="password")
        if st.form_submit_button("変更する", type="primary"):
            from utils import login_user
            if not login_user(st.session_state.user["username"], current_pw):
                st.error("現在のパスワードが違います。")
            elif s_new_pw != s_confirm_pw:
                st.error("新しいパスワードが一致しません。")
            elif len(s_new_pw) < 6:
                st.error("6文字以上で設定してください。")
            else:
                update_user(st.session_state.user["username"], password=s_new_pw)
                st.success("✅ パスワードを変更しました。次回ログインから適用されます。")
