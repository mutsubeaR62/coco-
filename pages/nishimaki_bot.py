import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import apply_theme, require_login, page_header
import streamlit.components.v1 as components

apply_theme()
require_login()

page_header("🤖 西牧Bot", "AIチャットボット — 試作版")

st.markdown(
    "<div style='background:white;border-radius:14px;padding:20px 24px;"
    "box-shadow:0 2px 12px rgba(0,0,0,0.07);border-left:4px solid #e85d04;"
    "margin-bottom:20px;'>"
    "<p style='margin:0 0 8px;font-size:0.95rem;'>西牧Botの試作品です。<br>"
    "ログイン・テストの上、ぜひご意見をお聞かせください！</p>"
    "<p style='margin:0;font-size:0.85rem;color:#888;'>※ 新しいタブで開くか、下のプレビューでご利用いただけます。</p>"
    "</div>",
    unsafe_allow_html=True,
)

st.link_button("🔗 西牧Botを新しいタブで開く",
               "https://sks-chatbot.vercel.app/about",
               type="primary", use_container_width=True)

st.divider()
st.caption("プレビュー（ページによっては表示されない場合があります）")
components.iframe("https://sks-chatbot.vercel.app/about", height=650, scrolling=True)
