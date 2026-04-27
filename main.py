import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils import apply_theme, init_default_users, sidebar_user, ROLE_LABELS

st.set_page_config(
    page_title="CoCo壱番屋 スタッフアプリ",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="auto",
)
apply_theme()
init_default_users()

if "user" not in st.session_state:
    st.session_state.user = None

if st.session_state.user is None:
    pg = st.navigation(
        [st.Page("pages/login.py", title="ログイン", icon="🔑", default=True)],
        position="hidden",
    )
else:
    user = st.session_state.user
    sidebar_user()

    role = user.get("role", "kenshu")
    is_kenshu = role == "kenshu"

    main_pages = [
        st.Page("pages/home.py",      title="ホーム",           icon="🏠", default=True),
        st.Page("pages/manual.py",    title="マニュアル",       icon="📋"),
        st.Page("pages/training.py",  title="新人研修",         icon="🎓"),
        st.Page("pages/checklist.py", title="チェックリスト",   icon="✅"),
        st.Page("pages/shift.py",        title="シフト申請",       icon="📅"),
        st.Page("pages/profile.py",      title="マイプロフィール", icon="👤"),
        st.Page("pages/nishimaki_bot.py", title="西牧Bot",   icon="🤖"),
        st.Page("pages/cyber_mg.py",     title="Cyber MG", icon="💼"),
    ]
    # 研修以外だけ表示するページ
    if not is_kenshu:
        main_pages.insert(2, st.Page("pages/orders.py", title="発注管理", icon="📦"))

    nav = {"メインメニュー": main_pages}

    from utils import is_manager
    if is_manager(user):
        nav["管理者"] = [
            st.Page("pages/admin.py",        title="管理者設定",  icon="⚙️"),
            st.Page("pages/shift_manage.py", title="シフト管理",  icon="📋"),
        ]

    pg = st.navigation(nav)

pg.run()
