import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from utils import apply_theme, init_default_users, sidebar_user, ROLE_LABELS, get_user_by_username

st.set_page_config(
    page_title="CoCo壱番屋 スタッフアプリ",
    page_icon="🍛",
    layout="wide",
    initial_sidebar_state="auto",
)
apply_theme()

# ── PWA メタタグ ──────────────────────────────────────────────
_ICON_URL = "https://raw.githubusercontent.com/mutsubeaR62/coco-/main/static/icon-192.png"
st.markdown(f"""
<link rel="apple-touch-icon" href="{_ICON_URL}">
<script>
(function() {{
    var ICON = "{_ICON_URL}";
    function setHead(tag, attrs) {{
        var sel = tag + '[' + Object.keys(attrs)[0] + '="' + Object.values(attrs)[0] + '"]';
        if (document.querySelector(sel)) return;
        var el = document.createElement(tag);
        Object.entries(attrs).forEach(function(p) {{ el.setAttribute(p[0], p[1]); }});
        document.head.appendChild(el);
    }}
    setHead('link', {{rel:'manifest',        href:'/app/static/manifest.json'}});
    setHead('link', {{rel:'apple-touch-icon', href:ICON}});
    setHead('meta', {{name:'apple-mobile-web-app-capable',         content:'yes'}});
    setHead('meta', {{name:'apple-mobile-web-app-status-bar-style', content:'black-translucent'}});
    setHead('meta', {{name:'apple-mobile-web-app-title',            content:'CoCo壱番屋'}});
    setHead('meta', {{name:'theme-color',                           content:'#e85d04'}});
}})();
</script>
""", unsafe_allow_html=True)
init_default_users()

# サイドバー最上部にロゴ（大きめに表示）
_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "COCO-LOGO_20190127120302.png")
if os.path.exists(_logo_path):
    st.logo(_logo_path)
    st.markdown("""
<style>
[data-testid="stLogoSidebar"] {
    padding: 12px 12px 8px !important;
    min-height: 90px !important;
    display: flex !important;
    align-items: center !important;
}
[data-testid="stLogoSidebar"] img {
    height: 80px !important;
    width: auto !important;
    max-width: 220px !important;
    object-fit: contain !important;
}
/* ロゴホームボタンを透明にしてロゴに重ねる */
[data-testid="stLogoSidebar"] ~ div .logo-home-btn > button {
    position: absolute !important;
    top: 0; left: 0;
    width: 100%; height: 100px;
    background: transparent !important;
    border: none !important;
    color: transparent !important;
    cursor: pointer !important;
    z-index: 10 !important;
}
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

# Cookie からログイン状態を復元
try:
    import extra_streamlit_components as stx
    _cm = stx.CookieManager(key="main_cm")
    # ログアウト直後はCookie復元をスキップ（フラグを消費）
    _just_logged_out = st.session_state.pop("_logout", False)
    if st.session_state.user is None and not _just_logged_out:
        _saved = _cm.get("coco_login")
        if _saved:
            _u = get_user_by_username(_saved)
            if _u:
                st.session_state.user = _u
        elif not st.session_state.get("_cookie_checked"):
            # CookieManagerは非同期なので初回レンダリングではNoneを返す
            # フラグを立ててもう一度レンダリングすることでCookieを正しく読む
            st.session_state["_cookie_checked"] = True
            st.rerun()
    if st.session_state.user is not None:
        st.session_state["_cookie_checked"] = False
except Exception:
    pass

if st.session_state.user is None:
    pg = st.navigation(
        [st.Page("pages/login.py", title="ログイン", icon="🔑", default=True)],
        position="hidden",
    )
else:
    user = st.session_state.user

    # ロゴクリックでホームへ（サイドバー最上部に透明ボタン）
    sidebar_user()

    role = user.get("role", "kenshu")
    is_kenshu = role == "kenshu"

    main_pages = [
        st.Page("pages/home.py",       title="ホーム",           icon=":material/home:",          default=True),
        st.Page("pages/notices.py",    title="お知らせ",          icon=":material/campaign:"),
        st.Page("pages/manual.py",     title="マニュアル",        icon=":material/menu_book:"),
        st.Page("pages/training.py",   title="新人研修",          icon=":material/school:"),
        st.Page("pages/checklist.py",  title="チェックリスト",    icon=":material/checklist:"),
        st.Page("pages/shift.py",      title="シフト申請",        icon=":material/calendar_month:"),
        st.Page("pages/profile.py",    title="マイプロフィール",  icon=":material/person:"),
        st.Page("pages/incidents.py",  title="クレーム記録",      icon=":material/report:"),
        st.Page("pages/nishimaki_bot.py", title="西牧Bot",        icon=":material/smart_toy:"),
        st.Page("pages/cyber_mg.py",   title="Cyber MG",          icon=":material/work:"),
    ]
    if not is_kenshu:
        main_pages.insert(3, st.Page("pages/orders.py", title="発注管理", icon=":material/inventory_2:"))

    nav = {"メインメニュー": main_pages}

    from utils import is_manager
    if is_manager(user):
        nav["管理者"] = [
            st.Page("pages/admin.py",        title="管理者設定",  icon=":material/admin_panel_settings:"),
            st.Page("pages/shift_manage.py", title="シフト管理",  icon=":material/edit_calendar:"),
        ]

    pg = st.navigation(nav)

pg.run()
