import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_login, page_header,
                   get_shift_deadline, submit_shift_request, get_user_shift_request,
                   get_shift_schedule, get_all_users, get_employee_type)
from datetime import date, timedelta
import calendar

apply_theme()
require_login()

page_header("📅 シフト", "申請 & 確定シフト確認")

user  = st.session_state.user
today = date.today()

WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]
HOURS = list(range(9, 24))

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


tab_apply, tab_view = st.tabs(["📝 シフト申請", "📊 確定シフト確認"])

# ══════════════════════════════════════════════════════════════
# TAB: 確定シフト確認（全員閲覧可）
# ══════════════════════════════════════════════════════════════
with tab_view:
    all_users_v  = get_all_users()
    users_dict_v = {u["username"]: u for u in all_users_v}

    sel_date_v = st.date_input("日付を選択", value=today, key="view_date_staff")
    date_str_v = sel_date_v.strftime("%Y-%m-%d")
    wd_v  = WEEKDAY_JP[sel_date_v.weekday()]
    dc_v  = "color:#dc3545;" if sel_date_v.weekday() == 6 else (
            "color:#1e6ab5;" if sel_date_v.weekday() == 5 else "")
    st.markdown(
        f"<h4 style='{dc_v}'>{sel_date_v.year}年{sel_date_v.month}月"
        f"{sel_date_v.day}日（{wd_v}）</h4>",
        unsafe_allow_html=True,
    )

    sc_v     = get_shift_schedule(date_str_v)
    shifts_v = sc_v.get("shifts", {})

    if not shifts_v:
        st.info("この日の確定シフトはまだ公開されていません。")
    else:
        def _get_pds(si):
            if "periods" in si and si["periods"]:
                return si["periods"]
            s, e = si.get("start", ""), si.get("end", "")
            return [[s, e]] if s and e else []

        def _in_pds(pds, h):
            for p in pds:
                try:
                    sh, sm = map(int, p[0].split(":"))
                    eh, em = map(int, p[1].split(":"))
                    if (sh * 60 + sm) < (h + 1) * 60 and (eh * 60 + em) > h * 60:
                        return True
                except Exception:
                    pass
            return False

        sorted_v = sorted(
            shifts_v.items(),
            key=lambda x: (
                0 if get_employee_type(users_dict_v.get(x[0], {})) == "seishain" else 1,
                users_dict_v.get(x[0], {}).get("name", x[0]),
            ),
        )

        tbl_v = """
<style>
.stbl2{border-collapse:collapse;font-size:12px;width:100%;}
.stbl2 th,.stbl2 td{border:1px solid #ddd;padding:4px 3px;text-align:center;white-space:nowrap;}
.stbl2 .nc{text-align:left;min-width:80px;font-weight:600;background:#fafafa;}
.stbl2 .ac{text-align:left;min-width:100px;font-size:11px;color:#555;background:#fafafa;}
.stbl2 thead th{background:#f0f0f0;font-weight:700;}
.cb2{background:#5b4b97!important;}
.cs2{background:#1e6ab5!important;}
</style>
<div style="overflow-x:auto;">
<table class="stbl2"><thead><tr>
<th class="nc">名前</th><th class="ac">備考</th>
"""
        for h in HOURS:
            tbl_v += f"<th>{h}</th>"
        tbl_v += "</tr></thead><tbody>"

        for uname, si in sorted_v:
            ud   = users_dict_v.get(uname, {})
            name = ud.get("name", uname)
            emp  = get_employee_type(ud)
            cls  = "cs2" if emp == "seishain" else "cb2"
            note = si.get("note", "")
            pds  = _get_pds(si)
            tbl_v += f'<tr><td class="nc">{name}</td><td class="ac">{note}</td>'
            for h in HOURS:
                tbl_v += f'<td class="{cls}"></td>' if _in_pds(pds, h) else "<td></td>"
            tbl_v += "</tr>"
        tbl_v += "</tbody></table></div>"
        st.markdown(tbl_v, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# TAB: シフト申請
# ══════════════════════════════════════════════════════════════
with tab_apply:
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

    st.markdown("""
<style>
.shift-card {
    background: #fff; border-radius: 10px; padding: 10px 14px 8px;
    margin-bottom: 8px; border-left: 4px solid #e0e0e0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.shift-card-sun { border-left-color: #dc3545; }
.shift-card-sat { border-left-color: #1e6ab5; }
.shift-day-label { font-size: 1rem; font-weight: 700; margin-bottom: 6px; line-height: 1.3; }
.shift-day-sun { color: #dc3545; }
.shift-day-sat { color: #1e6ab5; }
</style>
""", unsafe_allow_html=True)

    new_entries = {}

    for day in days:
        date_str = day.strftime("%Y-%m-%d")
        wd  = WEEKDAY_JP[day.weekday()]
        ex  = existing_entries.get(date_str, {})

        label_text = f"{m_sel}/{day.day}（{wd}）"
        if day.weekday() == 6:
            label_cls = "shift-day-sun"
            card_cls  = "shift-card shift-card-sun"
        elif day.weekday() == 5:
            label_cls = "shift-day-sat"
            card_cls  = "shift-card shift-card-sat"
        else:
            label_cls = ""
            card_cls  = "shift-card"

        type_opts = ["未入力", "出勤", "希望OFF"]
        cur_type  = {"work": "出勤", "off": "希望OFF"}.get(ex.get("type", ""), "未入力")

        st.markdown(f"<div class='{card_cls}'>", unsafe_allow_html=True)
        st.markdown(f"<div class='shift-day-label {label_cls}'>{label_text}</div>",
                    unsafe_allow_html=True)
        entry_type = st.selectbox(
            "種別", type_opts, index=type_opts.index(cur_type),
            key=f"t_{date_str}", label_visibility="collapsed"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if entry_type == "出勤":
            col_s, col_e, col_n = st.columns([2, 2, 3])
            def_s = ex.get("start", "09:00") if ex.get("start") in TIME_OPTS else "09:00"
            def_e = ex.get("end",   "17:00") if ex.get("end")   in TIME_OPTS else "17:00"
            with col_s:
                st.caption("開始")
                start = st.selectbox("", TIME_OPTS, index=TIME_OPTS.index(def_s),
                                     key=f"s_{date_str}", label_visibility="collapsed")
            with col_e:
                st.caption("終了")
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
                "", value=ex.get("note", ""),
                placeholder="理由（任意）例: 授業があります",
                key=f"n_{date_str}", label_visibility="collapsed"
            )
            new_entries[date_str] = {"type": "off", "note": note}

    st.divider()

    if not past_deadline:
        if st.button("📤 シフト希望を送信", type="primary", use_container_width=True):
            submit_shift_request(user["username"], sel_ym, new_entries)
            st.success("✅ シフト希望を送信しました！")
            st.rerun()
    else:
        st.button("📤 シフト希望を送信（期限切れ）", disabled=True, use_container_width=True)
