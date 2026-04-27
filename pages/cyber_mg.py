import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import apply_theme, require_login, page_header
import streamlit.components.v1 as components

apply_theme()
require_login()

page_header("💼 Cyber MG", "管理システム")

st.link_button("🔗 Cyber MGを新しいタブで開く",
               "https://cyber-mg.com/login",
               type="primary", use_container_width=True)

st.divider()
st.caption("プレビュー（ページによっては表示されない場合があります）")
components.iframe("https://cyber-mg.com/login", height=650, scrolling=True)
