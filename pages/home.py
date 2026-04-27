import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from utils import (apply_theme, require_login, page_header, get_progress,
                   STAMPS, ROLE_LABELS, get_today_birthdays, coco_spec_badge,
                   get_coco_spec, is_manager, get_all_users)

apply_theme()
require_login()

user = st.session_state.user
username = user["username"]
role = user.get("role", "new")
progress = get_progress(username)
earned_stamps = set(progress.get("stamps", []))

page_header(
    f"おかえり、{user['name']}さん！ 🍛",
    f"今日も一日よろしく！ — {datetime.now().strftime('%Y年%m月%d日 (%a)')}"
)

# ─── 誕生日バナー ─────────────────────────────────────────────
_all_users = get_all_users()
_me = next((u for u in _all_users if u["username"] == username), user)
_today_mmdd = datetime.now().strftime("%m-%d")

# 自分の誕生日
if _me.get("birthday", "")[-5:] == _today_mmdd and _today_mmdd:
    st.markdown(
        "<div style='background:linear-gradient(135deg,#f9a825,#ff6f00);color:white;"
        "border-radius:14px;padding:16px 24px;text-align:center;font-size:1.2rem;"
        "font-weight:700;margin-bottom:12px;box-shadow:0 4px 14px rgba(249,168,37,0.4);'>"
        "🎂 お誕生日おめでとうございます！今日はあなたの特別な日です！🎉"
        "</div>",
        unsafe_allow_html=True,
    )
    st.balloons()

# 他のメンバーの誕生日
_bday_others = get_today_birthdays(exclude_username=username)
for _bp in _bday_others:
    spec_html = coco_spec_badge(get_coco_spec(_bp))
    st.markdown(
        f"<div style='background:white;border-radius:12px;padding:14px 20px;"
        f"box-shadow:0 2px 10px rgba(0,0,0,0.08);border-left:5px solid #f9a825;"
        f"margin-bottom:8px;display:flex;align-items:center;gap:12px;'>"
        f"<span style='font-size:1.8rem;'>🎂</span>"
        f"<div>"
        f"<span style='font-weight:700;font-size:1.05rem;'>{_bp['name']}さんの誕生日！</span>"
        f"<span style='color:#f9a825;margin-left:8px;'>おめでとう🎉</span><br>"
        f"<span style='font-size:13px;color:#666;'>CoCoスペ: {spec_html}</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )

# ─── メトリクス ───────────────────────────────────────────────
scores = progress.get("quiz_scores", [])
best_score = max(scores) if scores else 0
cl = progress.get("checklist_completions", {})
total_cl = sum(cl.values())
manual_read = len(progress.get("manual_read", []))
stamp_count = len(earned_stamps)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("🎯 クイズ最高得点", f"{best_score}/10", help="クイズの最高得点")
with c2:
    st.metric("✅ チェックリスト完了", f"{total_cl}回", help="チェックリストを完了した回数")
with c3:
    st.metric("📚 マニュアル既読", f"{manual_read}セクション", help="読んだマニュアルの数")
with c4:
    st.metric("🏅 スタンプ", f"{stamp_count}/{len(STAMPS)}個", help="獲得したスタンプ数")

st.divider()

# ─── スタンプ一覧 ─────────────────────────────────────────────
st.subheader("🏅 スタンプコレクション")
st.caption("達成するともらえるスタンプを集めよう！")

stamp_html = '<div class="stamp-grid">'
for key, info in STAMPS.items():
    locked = key not in earned_stamps
    cls = "locked" if locked else ""
    title = info["desc"] if not locked else f"🔒 {info['desc']}"
    stamp_html += f"""
<div class="stamp-item" title="{title}">
  <div class="stamp-circle {cls}">{info['emoji']}</div>
  <div class="stamp-name {cls}">{info['name']}</div>
</div>"""
stamp_html += "</div>"
st.markdown(stamp_html, unsafe_allow_html=True)

st.divider()

# ─── クイックアクセス ─────────────────────────────────────────
st.subheader("📌 クイックアクセス")

links = [
    ("📋", "マニュアル",      "pages/manual.py"),
    ("🎓", "新人研修",        "pages/training.py"),
    ("✅", "チェックリスト",  "pages/checklist.py"),
    ("📅", "シフト申請",      "pages/shift.py"),
    ("👤", "マイプロフィール","pages/profile.py"),
]
if role != "kenshu":
    links.insert(1, ("📦", "発注管理", "pages/orders.py"))
if is_manager(user):
    links.append(("📋", "シフト管理", "pages/shift_manage.py"))

st.markdown("""
<style>
.qa-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 10px;
    margin-bottom: 8px;
}
@media (max-width: 767px) {
    .qa-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
}
.qa-card {
    background: white; border-radius: 12px; padding: 14px 8px;
    text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    border-bottom: 3px solid #e85d04;
}
.qa-card .qa-icon { font-size: 1.8rem; }
.qa-card .qa-label { font-weight: 600; font-size: 0.8rem; margin-top: 6px; color: #333; }
</style>
""", unsafe_allow_html=True)

# カードと遷移ボタンを行ごとに並べる
n = len(links)
row_size = 3 if n <= 6 else 4
for row_start in range(0, n, row_size):
    row_links = links[row_start:row_start + row_size]
    cols = st.columns(len(row_links))
    for col, (icon, label, page_path) in zip(cols, row_links):
        with col:
            st.markdown(
                f"<div class='qa-card'>"
                f"<div class='qa-icon'>{icon}</div>"
                f"<div class='qa-label'>{label}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
            if st.button(label, key=f"qa_{page_path}", use_container_width=True):
                st.switch_page(page_path)

# ─── ロール別メッセージ ───────────────────────────────────────
st.divider()
if role == "kenshu":
    st.info("🌱 **研修中の方へ** — まずは「マニュアル」と「新人研修」から始めてみよう！わからないことがあれば先輩に遠慮なく聞いてね。")
elif is_manager(user):
    _all = get_all_users()
    _kenshu = [u for u in _all if u.get("role") == "kenshu"]
    st.info(f"⚙️ **管理者メニュー** — 現在の研修中メンバー: {len(_kenshu)}名。「管理者設定」からメンバー管理や進捗確認ができます。")
elif role == "mate":
    st.info("👍 **メイトの皆さんへ** — 発注やチェックリストをこのアプリで管理できます。研修メンバーのサポートもよろしく！")
else:
    st.info("👍 お疲れ様です！今日もよろしくお願いします。")

# ─── アプリの説明 ─────────────────────────────────────────────
with st.expander("📖 このアプリの使い方"):
    st.markdown("""
| ページ | 内容 |
|--------|------|
| 📋 マニュアル | 業務手順・接客・衛生管理などを確認できます |
| 📦 発注管理 | 食材の発注数を計算・記録できます |
| 🎓 新人研修 | フラッシュカード・クイズ・スタンプで楽しく学べます |
| ✅ チェックリスト | 開店・閉店・衛生などの確認チェックリストです |
| ⚙️ 管理者設定 | （管理者のみ）メンバー管理・進捗確認ができます |
""")
