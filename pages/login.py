import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import base64
from utils import (apply_theme, login_user, award_stamps, show_new_stamps,
                   add_user, get_secret_question, verify_secret_answer,
                   reset_password, SECRET_QUESTIONS, get_all_users, ROOT_DIR)

apply_theme()

def _logo_b64():
    for fname in ["COCO-LOGO_20190127120302.png", "coco_logo.png", "logo.png"]:
        p = os.path.join(ROOT_DIR, fname)
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return None

st.markdown("""
<style>
.login-wrap {
    max-width: 480px;
    margin: 0 auto;
}
@media (max-width: 767px) {
    .login-wrap { max-width: 100%; padding: 0 4px; }
}
</style>
<div class="login-wrap" id="login-wrap-start"></div>
""", unsafe_allow_html=True)

# CSSで中央寄せしつつ、Streamlitのウィジェットは通常配置
_, col, _ = st.columns([0.5, 3, 0.5])

with col:
    b64 = _logo_b64()
    if b64:
        st.markdown(f"""
<div style="text-align:center; margin: 32px 0 24px;">
  <img src="data:image/png;base64,{b64}"
       style="max-width:200px; width:60%; margin-bottom:8px;">
  <div style="font-size:0.95rem; color:#666; margin-top:4px;">スタッフ専用アプリ</div>
</div>
""", unsafe_allow_html=True)
    else:
        st.markdown("""
<div style="text-align:center; margin: 32px 0 24px;">
  <div style="font-size:3.6rem;">🍛</div>
  <div style="font-size:1.8rem; font-weight:700; color:#e85d04; margin-top:8px;">CoCo壱番屋</div>
  <div style="font-size:0.95rem; color:#666; margin-top:4px;">スタッフ専用アプリ</div>
</div>
""", unsafe_allow_html=True)

    tab_login, tab_register, tab_reset = st.tabs(["🔑 ログイン", "📝 新規登録", "🔓 パスワード忘れ"])

    # ════ ログイン ═══════════════════════════════════════════════
    with tab_login:
        with st.form("login_form"):
            username = st.text_input("ユーザー名", placeholder="例: tanaka123")
            password = st.text_input("パスワード", type="password", placeholder="パスワードを入力")
            submitted = st.form_submit_button("ログイン →", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.error("ユーザー名とパスワードを入力してください。")
            else:
                user = login_user(username, password)
                if user:
                    st.session_state.user = user
                    _, new_stamps = award_stamps(username)
                    show_new_stamps(new_stamps)
                    st.rerun()
                else:
                    st.error("❌ ユーザー名またはパスワードが違います。")

    # ════ 新規登録 ═══════════════════════════════════════════════
    with tab_register:
        st.markdown("##### アカウントを作成する")
        st.caption("登録後のステータスは「研修」になります。管理者がステータスを変更します。")

        with st.form("register_form"):
            r_name     = st.text_input("表示名（本名）", placeholder="例: 田中 太郎")
            r_username = st.text_input("ユーザー名", placeholder="半角英数字のみ 例: tanaka123")
            r_pw       = st.text_input("パスワード", type="password", placeholder="6文字以上")
            r_pw2      = st.text_input("パスワード（確認）", type="password", placeholder="もう一度入力")

            st.markdown("**秘密の質問**（パスワード忘れのときに使います）")
            r_question = st.selectbox("質問を選ぶ", SECRET_QUESTIONS)
            r_answer   = st.text_input("答え", placeholder="大文字・小文字は区別しません")

            reg_submitted = st.form_submit_button("アカウントを作成", use_container_width=True,
                                                   type="primary")

        if reg_submitted:
            if not all([r_name, r_username, r_pw, r_pw2, r_answer]):
                st.error("すべての項目を入力してください。")
            elif not r_username.isalnum():
                st.error("ユーザー名は半角英数字のみ使用できます。")
            elif len(r_pw) < 6:
                st.error("パスワードは6文字以上にしてください。")
            elif r_pw != r_pw2:
                st.error("パスワードが一致しません。")
            else:
                ok = add_user(r_username, r_pw, r_name, "kenshu",
                              secret_question=r_question, secret_answer=r_answer)
                if ok:
                    st.success(f"✅ アカウントを作成しました！ユーザー名: **{r_username}**")
                    st.info("「ログイン」タブからログインしてください。")
                else:
                    st.error("そのユーザー名は既に使われています。別のユーザー名を試してください。")

    # ════ パスワードリセット ══════════════════════════════════════
    with tab_reset:
        st.markdown("##### パスワードを忘れた場合")

        # Step 1: ユーザー名を入力
        reset_username = st.text_input("ユーザー名を入力", key="reset_uname",
                                        placeholder="例: tanaka123")

        if reset_username:
            question = get_secret_question(reset_username)
            if question is None:
                st.error("そのユーザー名は存在しません。")
            elif question == "":
                st.warning("このアカウントには秘密の質問が設定されていません。管理者に問い合わせてください。")
            else:
                st.markdown(f"**秘密の質問:** {question}")

                with st.form("reset_form"):
                    r_ans  = st.text_input("答え", type="password",
                                            placeholder="登録した答えを入力（大文字・小文字不問）")
                    r_new  = st.text_input("新しいパスワード", type="password",
                                            placeholder="6文字以上")
                    r_new2 = st.text_input("新しいパスワード（確認）", type="password")
                    reset_ok = st.form_submit_button("パスワードを変更する",
                                                      use_container_width=True, type="primary")

                if reset_ok:
                    if not all([r_ans, r_new, r_new2]):
                        st.error("すべての項目を入力してください。")
                    elif len(r_new) < 6:
                        st.error("パスワードは6文字以上にしてください。")
                    elif r_new != r_new2:
                        st.error("新しいパスワードが一致しません。")
                    elif not verify_secret_answer(reset_username, r_ans):
                        st.error("❌ 答えが違います。")
                    else:
                        reset_password(reset_username, r_new)
                        st.success("✅ パスワードを変更しました！ログインタブからログインしてください。")
