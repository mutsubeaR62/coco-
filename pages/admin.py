import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_admin, page_header,
                   get_all_users, add_user, delete_user, update_user,
                   get_progress, STAMPS, ROLE_LABELS, get_employee_type,
                   get_coco_spec, coco_spec_badge, SERVICE_LEVELS, COOKING_LEVELS,
                   get_store_settings, save_store_settings,
                   get_store_code, update_store_code, get_store_display_name,
                   save_snapshot, load_json, save_json, store_path, _STORE_FILES)

apply_theme()
require_admin()

page_header("⚙️ 管理者設定", "メンバー管理・進捗確認")

tab_members, tab_progress, tab_store, tab_data = st.tabs(["👥 メンバー管理", "📊 進捗確認", "🏪 店舗設定", "🗄️ データ管理"])

# ════ メンバー管理 ══════════════════════════════════════════════
with tab_members:
    users = get_all_users()
    current_username = st.session_state.user["username"]

    # 統計
    counts = {}
    for u in users:
        r = u.get("role", "new")
        counts[r] = counts.get(r, 0) + 1

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("管理者", counts.get("admin", 0))
    with c2:
        st.metric("代行", counts.get("daiko", 0))
    with c3:
        st.metric("メイト", counts.get("mate", 0) + counts.get("staff", 0))
    with c4:
        st.metric("研修", counts.get("kenshu", 0) + counts.get("new", 0))
    with c5:
        st.metric("合計", len(users))

    st.divider()

    # メンバー一覧
    st.markdown("#### メンバー一覧")
    for u in users:
        role_label = ROLE_LABELS.get(u.get("role", "new"), "")
        is_self    = u["username"] == current_username
        prog       = get_progress(u["username"])
        stamp_count = len(prog.get("stamps", []))
        scores     = prog.get("quiz_scores", [])
        spec       = get_coco_spec(u)

        with st.expander(f"{role_label}　{u['name']} (@{u['username']}){'　— 自分' if is_self else ''}"):

            # ── 1行目: 参加日 / 誕生日 / スタンプ / CoCoスペ（読み取り専用） ──
            _info_cols = st.columns([2, 2, 2, 3])
            _info_cols[0].markdown(f"<div style='font-size:.8rem;color:#888;'>参加日</div><div style='font-size:.9rem;'>{u.get('joined','不明')}</div>", unsafe_allow_html=True)
            _info_cols[1].markdown(f"<div style='font-size:.8rem;color:#888;'>誕生日</div><div style='font-size:.9rem;'>{u.get('birthday','') or '未設定'}</div>", unsafe_allow_html=True)
            _info_cols[2].markdown(f"<div style='font-size:.8rem;color:#888;'>スタンプ</div><div style='font-size:.9rem;'>{stamp_count}/{len(STAMPS)}個　{f'/ クイズ {max(scores)}/10' if scores else ''}</div>", unsafe_allow_html=True)
            _info_cols[3].markdown(f"<div style='font-size:.8rem;color:#888;'>CoCoスペ</div>" + coco_spec_badge(spec), unsafe_allow_html=True)

            st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)

            # ── 2行目: ステータス / 雇用 / 時給 / 接客 / 調理 ──────────────
            _roles   = ["kenshu", "mate", "daiko", "admin"]
            _cur_role = u.get("role", "kenshu") if u.get("role") in _roles else "mate"
            _emp_opts = ["baito", "seishain"]

            _ec1, _ec2, _ec3, _ec4, _ec5 = st.columns([2, 2, 2, 2, 2])
            new_role = _ec1.selectbox("ステータス", _roles,
                index=_roles.index(_cur_role),
                format_func=lambda x: ROLE_LABELS.get(x, x),
                key=f"role_{u['username']}")
            new_emp = _ec2.selectbox("雇用形態", _emp_opts,
                index=_emp_opts.index(get_employee_type(u)),
                format_func=lambda x: "バイト" if x == "baito" else "社員",
                key=f"emp_{u['username']}")
            new_wage = _ec3.number_input("時給 (¥)", value=int(u.get("hourly_wage", 1050)),
                step=10, min_value=500, key=f"wage_{u['username']}")
            _svc_opts  = [x if x else "未取得" for x in SERVICE_LEVELS]
            _ckng_opts = [x if x else "未取得" for x in COOKING_LEVELS]
            _cur_svc  = spec.get("service") or "未取得"
            _cur_ckng = spec.get("cooking") or "未取得"
            new_svc  = _ec4.selectbox("接客", _svc_opts,
                index=_svc_opts.index(_cur_svc) if _cur_svc in _svc_opts else 0,
                key=f"svc_{u['username']}")
            new_ckng = _ec5.selectbox("調理", _ckng_opts,
                index=_ckng_opts.index(_cur_ckng) if _cur_ckng in _ckng_opts else 0,
                key=f"ckng_{u['username']}")

            # ── 3行目: 誕生日 / ボタン ───────────────────────────────────
            _bc1, _bc2, _bc3 = st.columns([3, 1, 1])
            new_bday = _bc1.text_input("誕生日", value=u.get("birthday", "") or "",
                placeholder="例: 07-15 または 2002-07-15", key=f"bday_{u['username']}")
            with _bc2:
                st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
                if st.button("更新", key=f"update_{u['username']}", type="primary", use_container_width=True):
                    update_user(u["username"], role=new_role, employee_type=new_emp,
                                hourly_wage=new_wage, birthday=new_bday,
                                coco_spec={"service": None if new_svc == "未取得" else new_svc,
                                           "cooking": None if new_ckng == "未取得" else new_ckng})
                    st.success(f"✅ {u['name']}さんを更新しました。")
                    st.rerun()
            with _bc3:
                st.markdown("<div style='margin-top:26px'></div>", unsafe_allow_html=True)
                if not is_self:
                    _del_key = f"confirm_del_{u['username']}"
                    if not st.session_state.get(_del_key):
                        if st.button("🗑️ 削除", key=f"del_{u['username']}", use_container_width=True):
                            st.session_state[_del_key] = True
                            st.rerun()
                    else:
                        st.warning(f"**{u['name']}さんを削除しますか？**")
                        _dc1, _dc2 = st.columns(2)
                        if _dc1.button("はい", key=f"del_yes_{u['username']}", type="primary"):
                            save_snapshot(f"ユーザー削除: {u['name']}")
                            delete_user(u["username"])
                            st.session_state.pop(_del_key, None)
                            st.rerun()
                        if _dc2.button("キャンセル", key=f"del_no_{u['username']}"):
                            st.session_state.pop(_del_key, None)
                            st.rerun()

            # ── 所属店舗（タグ形式） ────────────────────────────────────
            st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
            _ucodes = u.get("store_codes") or [u.get("store_code") or "default"]
            _primary = u.get("store_code") or "default"

            # タグHTMLを組み立て
            _tag_html = "<div style='display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:6px;'>"
            _tag_html += "<span style='font-size:.8rem;color:#888;font-weight:600;'>🏪 所属店舗:</span>"
            for _sc in _ucodes:
                _sc_disp = get_store_display_name(_sc)
                _sc_label = f"{_sc_disp}{'　✅' if _sc == _primary else ''}"
                _sc_sub = f" ({_sc})" if _sc_disp != _sc else ""
                _tag_html += (
                    f"<span style='background:{'#fff3e0' if _sc==_primary else '#f0f0f0'};"
                    f"border:1px solid {'#e85d04' if _sc==_primary else '#ccc'};"
                    f"border-radius:20px;padding:3px 10px;font-size:.82rem;color:{'#e85d04' if _sc==_primary else '#555'};'>"
                    f"{_sc_label}{_sc_sub}</span>"
                )
            _tag_html += "</div>"
            st.markdown(_tag_html, unsafe_allow_html=True)

            # 追加・削除コントロール
            _sa1, _sa2, _sa3 = st.columns([3, 1, 1])
            _new_sc_val = _sa1.text_input("店舗コードを追加", key=f"add_sc_{u['username']}",
                placeholder="店舗コードを入力（相手の店舗設定で確認）",
                label_visibility="collapsed")
            with _sa2:
                if st.button("＋ 追加", key=f"add_sc_btn_{u['username']}", use_container_width=True):
                    _stripped = _new_sc_val.strip()
                    if _stripped and _stripped not in _ucodes:
                        update_user(u["username"], store_codes=_ucodes + [_stripped])
                        st.success(f"✅ {_stripped} を追加しました")
                        st.rerun()
                    elif _stripped in _ucodes:
                        st.warning("すでに所属しています。")
            with _sa3:
                if len(_ucodes) > 1:
                    _rm_opts = [c for c in _ucodes if c != _primary]
                    _rm_sel = st.selectbox("削除する店舗", _rm_opts,
                        key=f"rm_sc_sel_{u['username']}", label_visibility="collapsed")
                    if st.button("削除", key=f"rm_sc_btn_{u['username']}", use_container_width=True):
                        _new_codes = [c for c in _ucodes if c != _rm_sel]
                        update_user(u["username"], store_codes=_new_codes)
                        st.rerun()

    st.divider()
    st.markdown("#### 新しいメンバーを追加")
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
                success, err_msg = add_user(new_username, new_pw, new_name, new_role,
                                            employee_type=new_emp_type, hourly_wage=new_wage)
                if success:
                    try:
                        update_user(new_username,
                                    birthday=new_bday_add,
                                    coco_spec={
                                        "service": None if new_svc_add == "未取得" else new_svc_add,
                                        "cooking": None if new_ckng_add == "未取得" else new_ckng_add,
                                    })
                    except Exception:
                        pass
                    st.success(f"✅ {new_name}さん（@{new_username}）を追加しました！")
                    st.rerun()
                else:
                    st.error(f"❌ 追加に失敗しました: {err_msg}")
            else:
                st.error("すべての項目を入力してください。")

    st.divider()
    with st.expander("🔐 パスワード変更"):
        _pw_tab1, _pw_tab2 = st.tabs(["メンバーのパスワードをリセット", "自分のパスワードを変更"])
        with _pw_tab1:
            _pw_users = get_all_users()
            _pw_opts = {u["name"]: u["username"] for u in _pw_users}
            with st.form("reset_pw"):
                _pw_target = st.selectbox("対象メンバー", list(_pw_opts.keys()))
                _new_pw = st.text_input("新しいパスワード", type="password")
                _confirm_pw = st.text_input("確認（同じパスワードをもう一度）", type="password")
                if st.form_submit_button("パスワードを変更", type="primary"):
                    if not _new_pw:
                        st.error("パスワードを入力してください。")
                    elif _new_pw != _confirm_pw:
                        st.error("パスワードが一致しません。")
                    elif len(_new_pw) < 6:
                        st.error("パスワードは6文字以上にしてください。")
                    else:
                        update_user(_pw_opts[_pw_target], password=_new_pw)
                        st.success(f"✅ {_pw_target}さんのパスワードを変更しました。")
        with _pw_tab2:
            with st.form("self_pw"):
                _cur_pw = st.text_input("現在のパスワード", type="password")
                _s_new = st.text_input("新しいパスワード", type="password")
                _s_conf = st.text_input("確認", type="password")
                if st.form_submit_button("変更する", type="primary"):
                    from utils import login_user
                    if not login_user(st.session_state.user["username"], _cur_pw):
                        st.error("現在のパスワードが違います。")
                    elif _s_new != _s_conf:
                        st.error("新しいパスワードが一致しません。")
                    elif len(_s_new) < 6:
                        st.error("6文字以上で設定してください。")
                    else:
                        update_user(st.session_state.user["username"], password=_s_new)
                        st.success("✅ パスワードを変更しました。次回ログインから適用されます。")

# ════ 進捗確認 ══════════════════════════════════════════════════
with tab_progress:
    users = get_all_users()
    st.markdown("#### 全メンバーの進捗一覧")

    show_filter = st.selectbox("表示するメンバー",
                               ["全員", "研修のみ", "メイトのみ", "代行のみ", "管理者のみ"])
    role_filter_map = {
        "全員": None, "研修のみ": ("kenshu", "new"),
        "メイトのみ": ("mate", "staff"), "代行のみ": ("daiko",), "管理者のみ": ("admin",),
    }
    filtered_roles = role_filter_map[show_filter]

    for u in users:
        if filtered_roles and u.get("role", "kenshu") not in filtered_roles:
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

# ════ 店舗設定 ═══════════════════════════════════════════════════

# ════ 店舗設定 ═══════════════════════════════════════════════════
with tab_store:
    st.markdown("#### 🏪 店舗情報の設定")
    st.caption("アプリ内に表示される店舗名・店舗番号などを設定できます。")

    current_store = get_store_settings()

    with st.form("store_form"):
        s_name   = st.text_input("店舗名", value=current_store.get("store_name", "CoCo壱番屋"),
                                  placeholder="例: CoCo壱番屋")
        s_branch = st.text_input("店舗・支店名（任意）",
                                  value=current_store.get("store_branch", ""),
                                  placeholder="例: 豊田元町店 / 123号店")
        s_address = st.text_input("住所（任意）",
                                   value=current_store.get("address", ""),
                                   placeholder="例: 愛知県豊田市元町1-1")
        s_tel    = st.text_input("電話番号（任意）",
                                  value=current_store.get("tel", ""),
                                  placeholder="例: 0565-XX-XXXX")
        if st.form_submit_button("保存する", type="primary", use_container_width=True):
            save_store_settings(
                store_name=s_name,
                store_branch=s_branch,
                address=s_address,
                tel=s_tel,
            )
            st.success("✅ 店舗情報を保存しました！サイドバーに反映されます。")
            st.rerun()

    st.divider()
    st.markdown("**現在の設定**")
    store = get_store_settings()
    st.write(f"店舗名: **{store.get('store_name', '')}** {store.get('store_branch', '')}")
    if store.get("address"):
        st.write(f"住所: {store['address']}")
    if store.get("tel"):
        st.write(f"電話: {store['tel']}")

    st.divider()
    st.markdown("#### 店舗コードの設定")
    st.caption("店舗コードは他の店舗とデータを分けるための識別子です。スタッフが登録するときに使います。")
    _cur_sc = get_store_code()
    st.markdown(
        f"<div style='background:#fff3e0;border-left:4px solid #e85d04;border-radius:8px;"
        f"padding:14px 20px;margin-bottom:12px;'>"
        f"<div style='font-size:0.8rem;color:#888;margin-bottom:4px;'>このアプリの店舗コード</div>"
        f"<div style='font-size:1.6rem;font-weight:700;letter-spacing:2px;color:#e85d04;'>"
        f"{_cur_sc}</div>"
        f"<div style='font-size:0.78rem;color:#666;margin-top:6px;'>"
        f"他の店舗のスタッフをマルチ店舗で追加するときは、このコードを相手の管理者に伝えてください。</div>"
        f"</div>",
        unsafe_allow_html=True
    )

    if not st.session_state.get("confirm_sc_change"):
        with st.form("store_code_form"):
            _new_sc = st.text_input("新しい店舗コード",
                                     placeholder="例: toyota01 / nagoya_honcho",
                                     help="半角英数字・アンダースコア推奨。変更すると全メンバーと全データが新コードに移行されます。")
            if st.form_submit_button("店舗コードを変更"):
                if not _new_sc.strip():
                    st.error("コードを入力してください。")
                elif _new_sc.strip() == _cur_sc:
                    st.warning("現在と同じコードです。")
                else:
                    st.session_state["confirm_sc_change"] = _new_sc.strip()
                    st.rerun()
    else:
        _pending_sc = st.session_state["confirm_sc_change"]
        st.error(
            f"⚠️ **本当に店舗コードを変更しますか？**\n\n"
            f"「`{_cur_sc}`」→「`{_pending_sc}`」\n\n"
            f"- 全メンバーのデータが新コードに移行されます\n"
            f"- 現在ログイン中のメンバーは**再ログインが必要**になります\n"
            f"- **この操作は慎重に行ってください**"
        )
        _sc1, _sc2 = st.columns(2)
        if _sc1.button("✅ はい、変更する", type="primary", key="sc_yes"):
            save_snapshot(f"店舗コード変更: {_cur_sc} → {_pending_sc}")
            update_store_code(_cur_sc, _pending_sc)
            st.session_state.user["store_code"] = _pending_sc
            if "store_codes" in st.session_state.user:
                st.session_state.user["store_codes"] = [
                    _pending_sc if c == _cur_sc else c
                    for c in st.session_state.user["store_codes"]
                ]
            st.session_state.pop("confirm_sc_change", None)
            st.success(f"✅ 店舗コードを「{_pending_sc}」に変更しました。他のメンバーに再ログインを伝えてください。")
            st.rerun()
        if _sc2.button("キャンセル", key="sc_no"):
            st.session_state.pop("confirm_sc_change", None)
            st.rerun()

# ════ データ管理 ════════════════════════════════════════════════
with tab_data:
    import json
    from datetime import datetime as _dt

    st.markdown("#### 🗄️ データのバックアップ・リストア")

    # ── エクスポート ──────────────────────────────────────────────
    st.markdown("##### 📥 バックアップをダウンロード")
    st.caption("現在の店舗の全データをJSONファイルとして保存します。")

    _backup_data = {
        "created_at": _dt.now().isoformat(),
        "store_code": get_store_code(),
        "users": load_json("users.json", {"users": {}}),
        "store_data": {}
    }
    for _fname in _STORE_FILES:
        _d = load_json(store_path(_fname), None)
        if _d is not None:
            _backup_data["store_data"][_fname] = _d

    _backup_json = json.dumps(_backup_data, ensure_ascii=False, indent=2)
    _ts = _dt.now().strftime("%Y%m%d_%H%M")
    st.download_button(
        label="⬇️ バックアップをダウンロード",
        data=_backup_json,
        file_name=f"coco_backup_{get_store_code()}_{_ts}.json",
        mime="application/json",
        use_container_width=True,
        type="primary",
    )

    st.divider()

    # ── リストア ──────────────────────────────────────────────────
    st.markdown("##### 📤 バックアップから復元")
    st.caption("ダウンロードしたJSONファイルをアップロードして復元します。")
    st.warning("⚠️ 復元すると現在のデータが上書きされます。必ず先にバックアップを取ってください。")

    _uploaded = st.file_uploader("バックアップファイルを選択", type=["json"], key="restore_upload")

    if _uploaded:
        try:
            _restore_data = json.loads(_uploaded.read().decode("utf-8"))
            _restore_sc   = _restore_data.get("store_code", "不明")
            _restore_ts   = _restore_data.get("created_at", "不明")
            _restore_users_count = len((_restore_data.get("users") or {}).get("users", []))

            st.info(
                f"**バックアップ情報**\n\n"
                f"- 作成日時: {_restore_ts}\n"
                f"- 店舗コード: {_restore_sc}\n"
                f"- ユーザー数: {_restore_users_count}名"
            )

            if not st.session_state.get("confirm_restore"):
                if st.button("このバックアップで復元する", type="primary", key="restore_btn"):
                    st.session_state["confirm_restore"] = True
                    st.session_state["restore_payload"] = _restore_data
                    st.rerun()
            else:
                st.error("⚠️ **本当に復元しますか？現在のデータはすべて上書きされます。**")
                _r1, _r2 = st.columns(2)
                if _r1.button("✅ はい、復元する", type="primary", key="restore_yes"):
                    save_snapshot("バックアップから復元（復元前の状態）")
                    _payload = st.session_state.get("restore_payload", {})
                    # ユーザーデータを復元
                    if _payload.get("users"):
                        save_json("users.json", _payload["users"])
                    # 店舗データを復元
                    for _fname, _fdata in (_payload.get("store_data") or {}).items():
                        save_json(store_path(_fname), _fdata)
                    st.session_state.pop("confirm_restore", None)
                    st.session_state.pop("restore_payload", None)
                    st.success("✅ 復元が完了しました！ページを再読み込みしてください。")
                    st.rerun()
                if _r2.button("キャンセル", key="restore_no"):
                    st.session_state.pop("confirm_restore", None)
                    st.session_state.pop("restore_payload", None)
                    st.rerun()
        except Exception as _e:
            st.error(f"ファイルの読み込みに失敗しました: {_e}")

    st.divider()

    # ── 変更履歴 ──────────────────────────────────────────────────
    st.markdown("##### 🕐 変更履歴（直近10件）")
    st.caption("ユーザー削除・店舗コード変更・復元の直前に自動保存されます。")

    _log = load_json(store_path("audit_log.json"), {"snapshots": []})
    _snaps = _log.get("snapshots", [])

    if not _snaps:
        st.info("まだ変更履歴がありません。")
    else:
        for _i, _snap in enumerate(_snaps):
            _ts  = _snap.get("timestamp", "")[:16].replace("T", " ")
            _op  = _snap.get("operation", "不明")
            _who = _snap.get("operator", "不明")
            with st.expander(f"🕐 {_ts}　**{_op}**　by {_who}"):
                st.caption(f"スナップショットID: {_snap.get('id', '—')}")
                if not st.session_state.get(f"confirm_snap_{_i}"):
                    if st.button("この時点に戻す", key=f"snap_restore_{_i}"):
                        st.session_state[f"confirm_snap_{_i}"] = True
                        st.rerun()
                else:
                    st.error(f"⚠️ **「{_op}」の直前の状態に戻しますか？現在のデータは上書きされます。**")
                    _sr1, _sr2 = st.columns(2)
                    if _sr1.button("✅ はい、戻す", key=f"snap_yes_{_i}", type="primary"):
                        save_snapshot(f"履歴から復元（復元前）")
                        _sd = _snap.get("data", {})
                        if _sd.get("users"):
                            save_json("users.json", _sd["users"])
                        for _fn, _fd in (_sd.get("store_data") or {}).items():
                            save_json(store_path(_fn), _fd)
                        st.session_state.pop(f"confirm_snap_{_i}", None)
                        st.success("✅ 復元しました。ページを再読み込みしてください。")
                        st.rerun()
                    if _sr2.button("キャンセル", key=f"snap_no_{_i}"):
                        st.session_state.pop(f"confirm_snap_{_i}", None)
                        st.rerun()
