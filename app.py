import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import apply_theme, sidebar_user

apply_theme()

if not st.session_state.get("user"):
    pg = st.navigation([
        st.Page("pages/login.py", title="ログイン", icon="🔑")
    ])
else:
    user = st.session_state.user
    role = user.get("role", "")

    pages = [
        st.Page("pages/home.py",      title="ホーム",           icon="🏠"),
        st.Page("pages/orders.py",    title="発注管理",          icon="📦"),
        st.Page("pages/checklist.py", title="チェックリスト",    icon="✅"),
        st.Page("pages/shift.py",     title="シフト",            icon="📅"),
        st.Page("pages/manual.py",    title="マニュアル",        icon="📚"),
        st.Page("pages/stepup.py",    title="ステップアップ",    icon="📈"),
        st.Page("pages/training.py",  title="研修",              icon="🎓"),
        st.Page("pages/profile.py",   title="プロフィール",      icon="👤"),
        st.Page("pages/nishimaki_bot.py", title="にしまきBot",   icon="🤖"),
    ]

    if role in ("admin", "daiko"):
        pages.append(st.Page("pages/shift_manage.py", title="シフト管理", icon="🗓️"))

    if role == "admin":
        pages.append(st.Page("pages/admin.py",    title="管理者",     icon="👑"))
        pages.append(st.Page("pages/cyber_mg.py", title="サイバーMG", icon="💻"))

    sidebar_user()
    pg = st.navigation(pages)

pg.run()
