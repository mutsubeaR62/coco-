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

# 30分刻みの時間選択肢 08:00〜23:30
TIME_OPTS = []
for _h in range(8, 24):
    TIME_OPTS.append(f"{_h:02d}:00")
    TIME_OPTS.append(f"{_h:02d}:30")


def get_requestable_months():
    months = []
    # 当月（締切前なら申請可）
    cur = today.strftime("%Y-%m")
    dl = get_shift_deadline(cur)
    try:
        if today <= date.fromisoformat(dl):
            months.append((cur, dl))
    except Exception:
        pass
    # 翌月・翌々月
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

# 既存の申請を読み込む
existing = get_user_shift_request(user["username"], sel_ym)
existing_entries = existing.get("entries", {}) if existing else {}
if existing:
    st.success(f"✅ 申請済み（{existing.get('submitted_at', '')}）　← 再送信で上書きできます")

# カレンダー入力
num_days = calendar.monthrange(y_sel, m_sel)[1]
days = [date(y_sel, m_sel, d) for d in range(1, num_days + 1)]

st.markdown(f"### {y_sel}年{m_sel}月のシフト希望")
st.caption("「出勤」を選ぶと時間帯を入力できます。希望のない日は「未入力」のままでOKです。")

# ヘッダー行
h0, h1, h2, h3, h4 = st.columns([2, 2, 2, 2, 3])
h0.markdown("**日付**"); h1.markdown("**種別**")
h2.markdown("**開始**"); h3.markdown("**終了**"); h4.markdown("**備考**")

new_entries = {}

for day in days:
    date_str = day.strftime("%Y-%m-%d")
    wd = WEEKDAY_JP[day.weekday()]
    ex = existing_entries.get(date_str, {})

    c0, c1, c2, c3, c4 = st.columns([2, 2, 2, 2, 3])

    label = f"{m_sel}/{day.day}({wd})"
    if day.weekday() == 6:
        c0.markdown(f"<span style='color:#dc3545;font-weight:600'>{label}</span>",
                    unsafe_allow_html=True)
    elif day.weekday() == 5:
        c0.markdown(f"<span style='color:#1e6ab5;font-weight:600'>{label}</span>",
                    unsafe_allow_html=True)
    else:
        c0.write(label)

    type_opts = ["未入力", "出勤", "希望OFF"]
    cur_type = {"work": "出勤", "off": "希望OFF"}.get(ex.get("type", ""), "未入力")
    entry_type = c1.selectbox("", type_opts, index=type_opts.index(cur_type),
                               key=f"t_{date_str}", label_visibility="collapsed")

    if entry_type == "出勤":
        def_s = ex.get("start", "09:00") if ex.get("start") in TIME_OPTS else "09:00"
        def_e = ex.get("end", "17:00") if ex.get("end") in TIME_OPTS else "17:00"
        start = c2.selectbox("", TIME_OPTS, index=TIME_OPTS.index(def_s),
                              key=f"s_{date_str}", label_visibility="collapsed")
        end   = c3.selectbox("", TIME_OPTS, index=TIME_OPTS.index(def_e),
                              key=f"e_{date_str}", label_visibility="collapsed")
        note  = c4.text_input("", value=ex.get("note", ""), placeholder="例: 22時30分まで願い",
                               key=f"n_{date_str}", label_visibility="collapsed")
        new_entries[date_str] = {"type": "work", "start": start, "end": end, "note": note}

    elif entry_type == "希望OFF":
        note = c4.text_input("", value=ex.get("note", ""), placeholder="理由（任意）",
                              key=f"n_{date_str}", label_visibility="collapsed")
        new_entries[date_str] = {"type": "off", "note": note}

st.divider()

if not past_deadline:
    if st.button("📤 シフト希望を送信", type="primary", use_container_width=True):
        submit_shift_request(user["username"], sel_ym, new_entries)
        st.success("✅ シフト希望を送信しました！")
        st.rerun()
else:
    st.button("📤 シフト希望を送信（期限切れ）", disabled=True, use_container_width=True)
