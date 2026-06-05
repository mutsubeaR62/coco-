import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from utils import (apply_theme, require_login, page_header, get_progress,
                   STAMPS, ROLE_LABELS, get_today_birthdays, coco_spec_badge,
                   get_coco_spec, is_manager, get_all_users, load_json, save_json, store_path,
                   get_store_settings, get_shift_schedule)

apply_theme()
require_login()

user = st.session_state.user
username = user["username"]
role = user.get("role", "new")
progress = get_progress(username)
earned_stamps = set(progress.get("stamps", []))

_store = get_store_settings()
_store_name = _store.get("store_name", "CoCo壱番屋")
_store_branch = _store.get("store_branch", "")
_store_full = _store_name + (f" {_store_branch}" if _store_branch else "")

page_header(
    f"おかえり、{user['name']}さん！ 🍛",
    f"{_store_full} — {datetime.now().strftime('%Y年%m月%d日 (%a)')}"
)

# ─── 未読お知らせバナー ───────────────────────────────────────
def _unread_notices():
    today   = datetime.now().strftime("%Y-%m-%d")
    notices = load_json(store_path("notices.json"), {"notices": []})["notices"]
    count   = 0
    for n in notices:
        if username in n.get("reads", []):
            continue
        target = n.get("target", "all")
        if target == "all":
            count += 1
        elif isinstance(target, str) and target.startswith("shift:"):
            sched = get_shift_schedule(target.split(":", 1)[1])
            if username in sched.get("members", []):
                count += 1
        elif isinstance(target, list) and username in target:
            count += 1
    return count

_unread = _unread_notices()
if _unread > 0:
    st.markdown(
        f"<div style='background:#fff3e0;border:1.5px solid #e85d04;border-radius:12px;"
        f"padding:12px 18px;margin-bottom:12px;display:flex;align-items:center;gap:12px;'>"
        f"<span style='font-size:1.4rem;'>📢</span>"
        f"<div>"
        f"<span style='font-weight:700;color:#e85d04;'>未読のお知らせが {_unread} 件あります</span>"
        f"</div></div>",
        unsafe_allow_html=True,
    )
    if st.button("お知らせを確認する", type="primary"):
        st.switch_page("pages/notices.py")
    st.write("")

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

st.markdown("""
<style>
/* スマホでメトリクスを2列に */
@media (max-width: 767px) {
    [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {
        flex-wrap: wrap !important;
    }
    [data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="column"] {
        min-width: calc(50% - 6px) !important;
        flex: 1 1 calc(50% - 6px) !important;
    }
}
</style>
""", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("クイズ最高", f"{best_score}/10")
with c2:
    st.metric("チェックリスト", f"{total_cl}回")
with c3:
    st.metric("マニュアル既読", f"{manual_read}件")
with c4:
    st.metric("スタンプ", f"{stamp_count}/{len(STAMPS)}")

st.divider()

# ─── スタンプ一覧 ─────────────────────────────────────────────
st.subheader("スタンプコレクション")
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
st.subheader("クイックアクセス")

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
    st.info("**研修中の方へ** — まずは「マニュアル」と「新人研修」から始めてみよう！わからないことがあれば先輩に遠慮なく聞いてね。")
elif is_manager(user):
    _all = get_all_users()
    _kenshu = [u for u in _all if u.get("role") == "kenshu"]
    st.info(f"**管理者メニュー** — 現在の研修中メンバー: {len(_kenshu)}名。「管理者設定」からメンバー管理や進捗確認ができます。")
elif role == "mate":
    st.info("**メイトの皆さんへ** — 発注やチェックリストをこのアプリで管理できます。研修メンバーのサポートもよろしく！")
else:
    st.info("お疲れ様です！今日もよろしくお願いします。")

# ─── チームの目標 ─────────────────────────────────────────────
st.subheader("チームの目標")
_users_with_goals = [u for u in _all_users if (u.get("goal") or "").strip()]
if _users_with_goals:
    _gcols = st.columns(min(3, len(_users_with_goals)))
    for _gi, _gu in enumerate(_users_with_goals):
        with _gcols[_gi % 3]:
            _rl = ROLE_LABELS.get(_gu.get("role", ""), "")
            st.markdown(
                f"<div style='background:white;border-radius:12px;padding:14px 16px;"
                f"box-shadow:0 2px 10px rgba(0,0,0,0.07);border-top:3px solid #e85d04;"
                f"margin-bottom:10px;'>"
                f"<div style='font-weight:700;font-size:0.95rem;'>{_gu['name']}</div>"
                f"<div style='font-size:0.72rem;color:#888;margin-bottom:8px;'>{_rl}</div>"
                f"<div style='font-size:0.88rem;color:#333;line-height:1.6;'>🎯 {_gu['goal']}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )
else:
    st.caption("まだ目標を設定しているメンバーはいません。マイプロフィールから設定できます！")

st.divider()

# ─── アプリの説明 ─────────────────────────────────────────────
_DEFAULT_DESC = """\
| ページ | 内容 |
|--------|------|
| 📋 マニュアル | 業務手順・接客・調理・ソース量表・定数表を確認できます |
| 📦 発注管理 | 食材の発注数を計算・記録できます（メイト以上） |
| 🎓 新人研修 | フラッシュカード・クイズ・スタンプ・卒業チェックリスト |
| ✅ チェックリスト | 開店・接客・閉店・衛生などの日常チェックとステップアップ表 |
| 👤 マイプロフィール | 自分の情報確認・CoCoスペ・目標の設定 |
| ⚙️ 管理者設定 | メンバー管理・進捗確認・パスワード変更（管理者のみ） |
"""
_home_info = load_json(store_path("home_info.json"), {"description": _DEFAULT_DESC})
_desc_text = _home_info.get("description") or _DEFAULT_DESC

with st.expander("このアプリの使い方"):
    st.markdown(_desc_text)
    if is_manager(user):
        st.divider()
        st.caption("管理者: 説明文を編集できます（Markdown形式）")
        _new_desc = st.text_area("説明文", value=_desc_text, height=180,
                                  label_visibility="collapsed", key="home_desc_edit")
        if st.button("説明を保存", key="save_home_desc"):
            save_json(store_path("home_info.json"), {"description": _new_desc})
            st.success("保存しました！")
            st.rerun()

# ─── アカウント（一番下） ──────────────────────────────────────
st.divider()
with st.expander("⚙️ アカウント"):
    st.caption(f"ログイン中: **{user['name']}**（{username}）")
    col_lo1, col_lo2 = st.columns(2)
    with col_lo1:
        if st.button("🚪 ログアウト", use_container_width=True):
            st.session_state.user = None
            st.session_state["_logout"] = True
            try:
                import extra_streamlit_components as stx
                _cm2 = stx.CookieManager(key="main_cm")
                _cm2.delete("coco_login")
            except Exception:
                pass
            st.rerun()
    with col_lo2:
        if st.button("👤 プロフィール", use_container_width=True):
            st.switch_page("pages/profile.py")
