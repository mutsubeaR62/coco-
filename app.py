import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import apply_theme, sidebar_user, inject_device_detector, get_device

st.set_page_config(
    page_title="CoCo壱番屋",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()
inject_device_detector()

# デバイスタイプをセッションに保存（各ページで使える）
st.session_state.device = get_device()

if not st.session_state.get("user"):
    pg = st.navigation([
        st.Page("pages/login.py", title="ログイン", icon="🔑")
    ])
else:
    user = st.session_state.user
    role = user.get("role", "")

    general_pages = [
        st.Page("pages/home.py",          title="ホーム",           icon="🏠"),
        st.Page("pages/orders.py",        title="発注管理",          icon="📦"),
        st.Page("pages/checklist.py",     title="チェックリスト",    icon="✅"),
        st.Page("pages/shift.py",         title="シフト",            icon="📅"),
        st.Page("pages/manual.py",        title="マニュアル",        icon="📚"),
        st.Page("pages/stepup.py",        title="ステップアップ",    icon="📈"),
        st.Page("pages/training.py",      title="研修",              icon="🎓"),
        st.Page("pages/profile.py",       title="プロフィール",      icon="👤"),
        st.Page("pages/nishimaki_bot.py", title="西牧Bot",           icon="🤖"),
    ]

    manager_pages = []
    if role in ("admin", "daiko"):
        manager_pages.append(st.Page("pages/shift_manage.py", title="シフト管理", icon="🗓️"))
    if role == "admin":
        manager_pages.append(st.Page("pages/admin.py", title="管理者", icon="👑"))

    nav = {"": general_pages}
    if manager_pages:
        nav["管理者メニュー"] = manager_pages

    sidebar_user()
    pg = st.navigation(nav)

pg.run()
