import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_login, page_header,
                   get_shift_deadline, submit_shift_request, get_user_shift_request)
from datetime import date, timedelta
import calendar

apply_theme()
require_login()

page_header("📅 シフト申請", "希望シフトを入力してください")

user = st.session_state.user
today = date.today()

WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]

TIME_OPTS = []
for _h in range(8, 24):
    TIME_OPTS.append(f"{_h:02d}:00")
    TIME_OPTS.append(f"{_h:02d}:30")


def get_requestable_months():
    months = []
    cur = today.strftime("%Y-%m")
    dl = get_shift_deadline(cur)
    try:
        if today <= date.fromisoformat(dl):
            months.append((cur, dl))
    except Exception:
        pass
    for i in range(1, 3):
        d = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        ym = d.strftime("%Y-%m")
        months.append((ym, get_shift_deadline(ym)))
    return months


months = get_requestable_months()
if not months:
    st.info("現在申請できる月がありません。")
    st.stop()

month_labels = [
    f"{int(ym[:4])}年{int(ym[5:7])}月　（締切: {dl}）"
    for ym, dl in months
]
sel_idx = st.selectbox("申請する月を選択", range(len(months)),
                        format_func=lambda i: month_labels[i])
sel_ym, deadline_str = months[sel_idx]
y_sel, m_sel = int(sel_ym[:4]), int(sel_ym[5:7])

try:
    past_deadline = today > date.fromisoformat(deadline_str)
except Exception:
    past_deadline = False

if past_deadline:
    st.warning(f"⚠️ 申請期限（{deadline_str}）を過ぎています。管理者に延長を依頼してください。")

existing = get_user_shift_request(user["username"], sel_ym)
existing_entries = existing.get("entries", {}) if existing else {}
if existing:
    st.success(f"✅ 申請済み（{existing.get('submitted_at', '')}）← 再送信で上書きできます")

num_days = calendar.monthrange(y_sel, m_sel)[1]
days = [date(y_sel, m_sel, d) for d in range(1, num_days + 1)]

st.markdown(f"### {y_sel}年{m_sel}月のシフト希望")
st.caption("「出勤」を選ぶと時間帯を入力できます。希望のない日は「未入力」のままでOKです。")

# スマホ対応CSS
st.markdown("""
<style>
.shift-day-label {
    font-size: 1rem; font-weight: 700; padding-top: 6px; line-height: 1.3;
}
.shift-day-sun { color: #dc3545; }
.shift-day-sat { color: #1e6ab5; }
.shift-day-holi { color: #dc3545; }
.shift-row-sep { border: none; border-top: 1px solid #f0f0f0; margin: 2px 0 6px; }
@media (max-width: 767px) {
    .shift-day-label { font-size: 1.05rem !important; }
}
</style>
""", unsafe_allow_html=True)

new_entries = {}

for day in days:
    date_str = day.strftime("%Y-%m-%d")
    wd = WEEKDAY_JP[day.weekday()]
    ex = existing_entries.get(date_str, {})

    # 日付ラベルHTML（曜日で色分け）
    label_text = f"{m_sel}/{day.day}({wd})"
    if day.weekday() == 6:
        date_html = f"<div class='shift-day-label shift-day-sun'>{label_text}</div>"
    elif day.weekday() == 5:
        date_html = f"<div class='shift-day-label shift-day-sat'>{label_text}</div>"
    else:
        date_html = f"<div class='shift-day-label'>{label_text}</div>"

    # ── 行1: 日付 ＋ 種別 ──────────────────────────────────────
    col_date, col_type = st.columns([2, 3])
    with col_date:
        st.markdown(date_html, unsafe_allow_html=True)

    type_opts = ["未入力", "出勤", "希望OFF"]
    cur_type = {"work": "出勤", "off": "希望OFF"}.get(ex.get("type", ""), "未入力")
    entry_type = col_type.selectbox(
        "", type_opts, index=type_opts.index(cur_type),
        key=f"t_{date_str}", label_visibility="collapsed"
    )

    # ── 行2: 時間・備考（出勤時のみ）─────────────────────────
    if entry_type == "出勤":
        col_s, col_e, col_n = st.columns([2, 2, 3])
        def_s = ex.get("start", "09:00") if ex.get("start") in TIME_OPTS else "09:00"
        def_e = ex.get("end", "17:00") if ex.get("end") in TIME_OPTS else "17:00"
        with col_s:
            st.caption("開始時刻")
            start = st.selectbox("", TIME_OPTS, index=TIME_OPTS.index(def_s),
                                  key=f"s_{date_str}", label_visibility="collapsed")
        with col_e:
            st.caption("終了時刻")
            end = st.selectbox("", TIME_OPTS, index=TIME_OPTS.index(def_e),
                                key=f"e_{date_str}", label_visibility="collapsed")
        with col_n:
            st.caption("備考")
            note = st.text_input("", value=ex.get("note", ""),
                                  placeholder="例: 22時まで",
                                  key=f"n_{date_str}", label_visibility="collapsed")
        new_entries[date_str] = {"type": "work", "start": start, "end": end, "note": note}

    elif entry_type == "希望OFF":
        note = st.text_input(
            "理由（任意）", value=ex.get("note", ""),
            placeholder="例: 授業があります",
            key=f"n_{date_str}"
        )
        new_entries[date_str] = {"type": "off", "note": note}

    st.markdown("<hr class='shift-row-sep'>", unsafe_allow_html=True)

st.divider()

if not past_deadline:
    if st.button("📤 シフト希望を送信", type="primary", use_container_width=True):
        submit_shift_request(user["username"], sel_ym, new_entries)
        st.success("✅ シフト希望を送信しました！")
        st.rerun()
else:
    st.button("📤 シフト希望を送信（期限切れ）", disabled=True, use_container_width=True)
