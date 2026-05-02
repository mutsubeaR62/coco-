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

# 30分刻み
HALF_SLOTS = [(h, m) for h in range(9, 24) for m in (0, 30)]
TIME_OPTS  = [f"{h:02d}:{m:02d}" for h in range(8, 25) for m in (0, 30)]

SHIFT_TYPES = ["自店舗", "レギュラー", "欠員", "地店舗ヘルプ", "発注", "ごみ捨て"]
TYPE_COLORS = {
    "自店舗":       "#5b4b97",
    "レギュラー":   "#1e6ab5",
    "欠員":         "#dc3545",
    "地店舗ヘルプ": "#e83e8c",
    "発注":         "#f48c06",
    "ごみ捨て":     "#28a745",
}


def get_periods(si):
    if "periods" in si and si["periods"]:
        return si["periods"]
    s, e = si.get("start", ""), si.get("end", "")
    return [[s, e]] if s and e else []


def slot_in_periods(periods, h, m):
    ss, se = h * 60 + m, h * 60 + m + 30
    for p in periods:
        try:
            sh, sm = map(int, p[0].split(":"))
            eh, em = map(int, p[1].split(":"))
            if (sh * 60 + sm) < se and (eh * 60 + em) > ss:
                return True
        except Exception:
            pass
    return False


def calc_hours(periods):
    total = 0
    for p in periods:
        try:
            sh, sm = map(int, p[0].split(":"))
            eh, em = map(int, p[1].split(":"))
            total += (eh * 60 + em) - (sh * 60 + sm)
        except Exception:
            pass
    return total / 60


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

    # 月選択
    month_opts_v = []
    for i in range(-1, 4):
        d = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        month_opts_v.append(d.strftime("%Y-%m"))
    sel_month_v = st.selectbox(
        "月を選択", month_opts_v, index=1,
        format_func=lambda m: f"{m[:4]}年{int(m[5:7])}月",
        key="view_month_staff",
    )
    y_v, m_v = int(sel_month_v[:4]), int(sel_month_v[5:7])
    num_days_v = calendar.monthrange(y_v, m_v)[1]

    # 凡例
    leg_html = "<div style='display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 14px;font-size:12px;'>"
    for t, c in TYPE_COLORS.items():
        leg_html += f"<span style='background:{c};color:#fff;padding:2px 9px;border-radius:4px;'>{t}</span>"
    leg_html += "</div>"
    st.markdown(leg_html, unsafe_allow_html=True)

    # CSSは1回だけ出力
    st.markdown("""
<style>
.sv-wrap { margin-bottom: 20px; }
.sv-hdr  { font-size: 1rem; font-weight: 700; padding: 6px 12px;
           background: #f8f9fa; border-left: 3px solid #e85d04;
           border-radius: 6px 6px 0 0; color: #222; }
.sv-sun  { border-left-color: #dc3545 !important; color: #dc3545; }
.sv-sat  { border-left-color: #1e6ab5 !important; color: #1e6ab5; }
.sv-memo { background:#fffdf0; border:1px solid #f0c060; border-radius:4px;
           padding:4px 10px; font-size:0.82rem; color:#555; margin:4px 0 6px; }
.sv-none { font-size: 0.82rem; color: #bbb; padding: 4px 12px 8px;
           background: #fafafa; border-radius: 0 0 6px 6px; }
.s30v    { border-collapse:collapse; font-size:12px; width:100%; }
.s30v th,.s30v td { border:1px solid #e8e8e8; padding:4px 0; text-align:center; white-space:nowrap; color:#333; }
.s30v .nc { text-align:left; min-width:72px; font-weight:600; background:#fafafa; padding:4px 8px; color:#222; }
.s30v .ac { text-align:left; min-width:60px; font-size:11px; color:#666; background:#fafafa; padding:4px 5px; }
.s30v .hh { min-width:14px; width:14px; }
.s30v .tw { min-width:34px; font-weight:600; color:#444; }
.s30v .oh { border-left:1px solid #bbb !important; }
.s30v thead th { background:#f5f5f5; font-weight:600; color:#555; font-size:11px; }
.s30v .cnt-low { color:#dc3545 !important; font-weight:700; }
</style>
""", unsafe_allow_html=True)

    for day_num in range(1, num_days_v + 1):
        d  = date(y_v, m_v, day_num)
        ds = d.strftime("%Y-%m-%d")
        wd = WEEKDAY_JP[d.weekday()]

        if d.weekday() == 6:
            hdr_cls = "sv-hdr sv-sun"
        elif d.weekday() == 5:
            hdr_cls = "sv-hdr sv-sat"
        else:
            hdr_cls = "sv-hdr"

        sc_day   = get_shift_schedule(ds)
        shifts_d = sc_day.get("shifts", {})
        memo_d   = sc_day.get("memo", "")

        html_day = f"<div class='sv-wrap'>"
        html_day += f"<div class='{hdr_cls}'>{m_v}/{day_num}（{wd}）</div>"

        if memo_d:
            html_day += f"<div class='sv-memo'>📝 {memo_d}</div>"

        if not shifts_d:
            html_day += "<div class='sv-none'>— 未登録 —</div>"
        else:
            sorted_d = sorted(
                shifts_d.items(),
                key=lambda x: (
                    0 if get_employee_type(users_dict_v.get(x[0], {})) == "seishain" else 1,
                    users_dict_v.get(x[0], {}).get("name", x[0]),
                ),
            )

            # 人員数カウント
            count_per_slot = {(h, m): 0 for h, m in HALF_SLOTS}
            for uname, si in shifts_d.items():
                pds = get_periods(si)
                for h, m in HALF_SLOTS:
                    if slot_in_periods(pds, h, m):
                        count_per_slot[(h, m)] += 1

            html_day += "<div style='overflow-x:auto;'><table class='s30v'><thead><tr>"
            html_day += "<th class='nc'>名前</th><th class='ac'>備考</th>"
            for h in range(9, 24):
                html_day += f'<th class="oh" colspan="2">{h}</th>'
            html_day += "<th class='tw'>時間</th></tr></thead><tbody>"

            for uname, si in sorted_d:
                ud    = users_dict_v.get(uname, {})
                name  = ud.get("name", uname)
                note  = si.get("note", "")
                stype = si.get("type", "自店舗")
                color = TYPE_COLORS.get(stype, "#5b4b97")
                pds   = get_periods(si)
                hrs   = calc_hours(pds)

                html_day += f'<tr><td class="nc">{name}</td><td class="ac">{note}</td>'
                for h, m in HALF_SLOTS:
                    cls = "hh oh" if m == 0 else "hh"
                    if slot_in_periods(pds, h, m):
                        html_day += f'<td class="{cls}" style="background:{color}"></td>'
                    else:
                        html_day += f'<td class="{cls}"></td>'
                html_day += f'<td class="tw">{hrs:.1f}</td></tr>'

            # 人員数行
            html_day += '<tr style="border-top:2px solid #999;">'
            html_day += '<td class="nc" colspan="2" style="font-weight:700;color:#666;padding:3px 6px;">人員数</td>'
            for h, m in HALF_SLOTS:
                c   = count_per_slot[(h, m)]
                cls = "hh oh" if m == 0 else "hh"
                if 0 < c < int(sc_day.get("min_staff", 3)):
                    html_day += f'<td class="{cls} cnt-low">{c}</td>'
                else:
                    html_day += f'<td class="{cls}">{c if c else ""}</td>'
            html_day += '<td class="tw"></td></tr>'

            html_day += "</tbody></table></div>"

        html_day += "</div>"
        st.markdown(html_day, unsafe_allow_html=True)


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
