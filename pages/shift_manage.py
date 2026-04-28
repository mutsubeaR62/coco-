import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_manager, page_header,
                   get_all_users, get_all_shift_requests, get_shift_schedule,
                   save_shift_schedule, get_shift_deadline, set_shift_deadline,
                   get_employee_type, get_coco_spec, coco_spec_badge)
from datetime import date, timedelta, datetime
import calendar

apply_theme()
require_manager()

page_header("📋 シフト管理", "シフト確認・作成・申請管理")

today = date.today()
WEEKDAY_JP = ["月", "火", "水", "木", "金", "土", "日"]
HOURS = list(range(9, 24))  # 9〜23時

TIME_OPTS = []
for _h in range(8, 24):
    TIME_OPTS.append(f"{_h:02d}:00")
    TIME_OPTS.append(f"{_h:02d}:30")


def get_periods(si):
    """シフトデータから periods リストを返す（旧形式 start/end にも対応）"""
    if "periods" in si and si["periods"]:
        return si["periods"]
    s, e = si.get("start", ""), si.get("end", "")
    if s and e:
        return [[s, e]]
    return []

def hour_in_periods(periods, hour):
    """複数の勤務時間帯のいずれかにその時間が含まれるか"""
    for period in periods:
        try:
            sh, sm = map(int, period[0].split(":"))
            eh, em = map(int, period[1].split(":"))
            if (sh * 60 + sm) < (hour + 1) * 60 and (eh * 60 + em) > hour * 60:
                return True
        except Exception:
            pass
    return False

def calc_labor_hours(periods):
    total_mins = 0
    for period in periods:
        try:
            sh, sm = map(int, period[0].split(":"))
            eh, em = map(int, period[1].split(":"))
            total_mins += (eh * 60 + em) - (sh * 60 + sm)
        except Exception:
            pass
    return total_mins / 60

def hour_bools_to_periods(hour_bools):
    """連続するTrueの時間帯をperiods形式に変換"""
    periods = []
    in_period = False
    start_h = None
    for h in HOURS:
        if hour_bools.get(h, False):
            if not in_period:
                start_h = h
                in_period = True
        else:
            if in_period:
                periods.append([f"{start_h:02d}:00", f"{h:02d}:00"])
                in_period = False
    if in_period:
        periods.append([f"{start_h:02d}:00", f"{HOURS[-1]+1:02d}:00"])
    return periods


def render_grid(schedule, users_dict):
    shifts = schedule.get("shifts", {})
    min_staff = int(schedule.get("min_staff", 3))
    sales_target = float(schedule.get("sales_target", 0))

    # 人件費計算・時間帯ごとの人数集計
    total_labor = 0.0
    count_per_hour = {h: 0 for h in HOURS}
    for uname, si in shifts.items():
        ud = users_dict.get(uname, {})
        wage = float(ud.get("hourly_wage", 1050))
        periods = get_periods(si)
        total_labor += calc_labor_hours(periods) * wage
        for h in HOURS:
            if hour_in_periods(periods, h):
                count_per_hour[h] += 1

    ratio = (total_labor / sales_target * 100) if sales_target > 0 else None

    # 上部メトリクス
    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("売上目標", f"¥{sales_target:,.0f}")
    mc2.metric("人件費見込み", f"¥{total_labor:,.0f}")
    mc3.metric("人件費率", f"{ratio:.1f}%" if ratio is not None else "—")

    if not shifts:
        st.info("この日のシフトはまだ登録されていません。")
        return

    # 色凡例
    st.markdown(
        "<div style='display:flex;gap:16px;margin:6px 0 10px;font-size:13px;'>"
        "<span style='background:#5b4b97;color:#fff;padding:2px 10px;border-radius:4px;'>バイト</span>"
        "<span style='background:#1e6ab5;color:#fff;padding:2px 10px;border-radius:4px;'>社員</span>"
        "<span style='border-bottom:3px solid #dc3545;padding:2px 10px;'>人員不足</span>"
        "</div>",
        unsafe_allow_html=True,
    )

    # HTMLテーブル
    tbl = """
<style>
.stbl{border-collapse:collapse;font-size:13px;width:100%;}
.stbl th,.stbl td{border:1px solid #ddd;padding:5px 4px;text-align:center;white-space:nowrap;}
.stbl .nc{text-align:left;min-width:88px;font-weight:600;background:#fafafa;}
.stbl .ac{text-align:left;min-width:130px;font-size:11px;color:#555;background:#fafafa;}
.stbl .hc{min-width:38px;}
.stbl thead th{background:#f0f0f0;font-weight:700;}
.cb{background:#5b4b97!important;color:#fff;}
.cs{background:#1e6ab5!important;color:#fff;}
.low{color:#dc3545;font-weight:700;border-bottom:3px solid #dc3545!important;}
</style>
<div style="overflow-x:auto;">
<table class="stbl"><thead><tr>
<th class="nc">名前</th><th class="ac">備考</th>
"""
    for h in HOURS:
        tbl += f'<th class="hc">{h}</th>'
    tbl += "</tr></thead><tbody>"

    # 社員→バイトの順でソート
    sorted_shifts = sorted(
        shifts.items(),
        key=lambda x: (
            0 if get_employee_type(users_dict.get(x[0], {})) == "seishain" else 1,
            users_dict.get(x[0], {}).get("name", x[0]),
        ),
    )

    for uname, si in sorted_shifts:
        ud = users_dict.get(uname, {})
        name = ud.get("name", uname)
        emp = get_employee_type(ud)
        cls = "cs" if emp == "seishain" else "cb"
        note = si.get("note", "")
        periods = get_periods(si)
        tbl += f'<tr><td class="nc">{name}</td><td class="ac">{note}</td>'
        for h in HOURS:
            if hour_in_periods(periods, h):
                tbl += f'<td class="{cls}"></td>'
            else:
                tbl += "<td></td>"
        tbl += "</tr>"

    # 人員数行
    tbl += '<tr style="border-top:2px solid #999;"><td class="nc" colspan="2" style="font-weight:700;color:#666;">人員数</td>'
    for h in HOURS:
        c = count_per_hour[h]
        if 0 < c < min_staff:
            tbl += f'<td class="low">{c}</td>'
        else:
            tbl += f'<td style="font-weight:600;">{c if c else ""}</td>'
    tbl += "</tr></tbody></table></div>"

    st.markdown(tbl, unsafe_allow_html=True)


# ═══ タブ ══════════════════════════════════════════════════════
tab_view, tab_req, tab_cfg = st.tabs(["📊 シフト確認", "📥 申請管理", "⚙️ 設定"])

all_users = get_all_users()
users_dict = {u["username"]: u for u in all_users}

# ─── シフト確認 & 編集 ────────────────────────────────────────
with tab_view:
    import pandas as pd

    # 月選択
    month_opts_m = []
    for i in range(-1, 4):
        d = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        month_opts_m.append(d.strftime("%Y-%m"))
    sel_month_m = st.selectbox(
        "月を選択", month_opts_m, index=1,
        format_func=lambda m: f"{m[:4]}年{int(m[5:7])}月",
        key="view_month_mgr",
    )
    y_m, m_m = int(sel_month_m[:4]), int(sel_month_m[5:7])
    num_days_m = calendar.monthrange(y_m, m_m)[1]

    all_requests_m = get_all_shift_requests(sel_month_m)

    # 月全体の人件費サマリ
    total_labor_m = 0.0
    for day_num in range(1, num_days_m + 1):
        sc_tmp = get_shift_schedule(date(y_m, m_m, day_num).strftime("%Y-%m-%d"))
        for si in sc_tmp.get("shifts", {}).values():
            ud_tmp = {}
            for uname_tmp, si_tmp in sc_tmp.get("shifts", {}).items():
                if si_tmp is si:
                    ud_tmp = users_dict.get(uname_tmp, {})
            wage = float(ud_tmp.get("hourly_wage", 1050))
            total_labor_m += calc_labor_hours(get_periods(si)) * wage
    st.metric("今月の人件費合計（概算）", f"¥{total_labor_m:,.0f}")

    st.divider()

    # 1か月分を縦に表示（各日ごとにグリッド＋編集）
    for day_num in range(1, num_days_m + 1):
        d   = date(y_m, m_m, day_num)
        ds  = d.strftime("%Y-%m-%d")
        wd  = WEEKDAY_JP[d.weekday()]
        dc  = "color:#dc3545;" if d.weekday() == 6 else (
              "color:#1e6ab5;" if d.weekday() == 5 else "color:#333;")

        schedule_d = get_shift_schedule(ds)
        shifts_d   = schedule_d.get("shifts", {})

        # 日付ヘッダー
        st.markdown(
            f"<div style='font-size:1.05rem;font-weight:700;{dc}"
            f"padding:6px 0 2px;border-bottom:2px solid #eee;margin-top:12px;'>"
            f"{m_m}/{day_num}（{wd}）</div>",
            unsafe_allow_html=True,
        )

        if shifts_d:
            render_grid(schedule_d, users_dict)
        else:
            st.caption("— 未登録 —")

        # 編集エリア（expander で折りたたみ）
        with st.expander(f"✏️ {m_m}/{day_num} を編集"):
            # 売上目標・最低人員
            cs1, cs2 = st.columns(2)
            new_target = cs1.number_input("売上目標 (¥)",
                                           value=int(schedule_d.get("sales_target", 0)),
                                           step=1000, min_value=0, key=f"tgt_{ds}")
            new_min    = cs2.number_input("最低必要人員",
                                           value=int(schedule_d.get("min_staff", 3)),
                                           step=1, min_value=1, key=f"minst_{ds}")
            if st.button("設定保存", key=f"cfg_{ds}"):
                schedule_d["sales_target"] = new_target
                schedule_d["min_staff"]    = new_min
                save_shift_schedule(ds, schedule_d)
                st.success("保存しました")
                st.rerun()

            st.divider()

            # グリッド編集
            req_for_day = {
                uname: req["entries"][ds]
                for uname, req in all_requests_m.items()
                if ds in req.get("entries", {})
                and req["entries"][ds].get("type") == "work"
            }
            target_unames = sorted(
                set(shifts_d.keys()) | set(req_for_day.keys()),
                key=lambda u: (
                    0 if get_employee_type(users_dict.get(u, {})) == "seishain" else 1,
                    users_dict.get(u, {}).get("name", u),
                ),
            )

            if not target_unames:
                st.caption("申請・登録済みのスタッフがいません。")
            else:
                rows = {}
                name_to_uname = {}
                for uname in target_unames:
                    ud   = users_dict.get(uname, {})
                    name = ud.get("name", uname)
                    name_to_uname[name] = uname
                    si   = shifts_d.get(uname, {})
                    pds  = get_periods(si)
                    if not pds and uname in req_for_day:
                        e   = req_for_day[uname]
                        pds = [[e.get("start", "09:00"), e.get("end", "17:00")]]
                    row = {str(h): hour_in_periods(pds, h) for h in HOURS}
                    row["備考"] = si.get("note", "") or req_for_day.get(uname, {}).get("note", "")
                    rows[name] = row

                df = pd.DataFrame(rows).T
                df.index.name = "名前"

                col_cfg = {str(h): st.column_config.CheckboxColumn(
                    f"{h}", default=False, width="small") for h in HOURS}
                col_cfg["備考"] = st.column_config.TextColumn("備考", width="medium")

                st.caption("チェックを外すと休憩になります。")
                edited = st.data_editor(
                    df, column_config=col_cfg,
                    use_container_width=True, key=f"grid_{ds}"
                )

                if st.button("💾 シフトを保存", type="primary", key=f"save_{ds}"):
                    sc_save = get_shift_schedule(ds)
                    sc_save.setdefault("shifts", {})
                    for name, row in edited.iterrows():
                        uname = name_to_uname.get(name)
                        if not uname:
                            continue
                        hour_bools = {h: bool(row[str(h)]) for h in HOURS}
                        new_pds = hour_bools_to_periods(hour_bools)
                        if new_pds:
                            sc_save["shifts"][uname] = {
                                "periods": new_pds,
                                "note": str(row.get("備考", "") or ""),
                            }
                        else:
                            sc_save["shifts"].pop(uname, None)
                    sc_save["sales_target"] = new_target
                    sc_save["min_staff"]    = new_min
                    save_shift_schedule(ds, sc_save)
                    st.success("✅ 保存しました！")
                    st.rerun()

# ─── 申請管理 ──────────────────────────────────────────────────
with tab_req:
    st.markdown("#### スタッフのシフト申請一覧")

    month_list = []
    for i in range(-1, 3):
        d = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        month_list.append(d.strftime("%Y-%m"))

    sel_month = st.selectbox("月を選択", month_list,
                              format_func=lambda m: f"{m[:4]}年{int(m[5:7])}月",
                              index=1, key="req_month")
    dl = get_shift_deadline(sel_month)
    st.info(f"📅 申請締切: {dl}")

    requests = get_all_shift_requests(sel_month)
    if not requests:
        st.info("まだ申請がありません。")
    else:
        for uname, req in requests.items():
            ud = users_dict.get(uname, {})
            name = ud.get("name", uname)
            entries = req.get("entries", {})
            work_days = sum(1 for e in entries.values() if e.get("type") == "work")
            off_days  = sum(1 for e in entries.values() if e.get("type") == "off")

            spec_html = coco_spec_badge(get_coco_spec(ud))
            with st.expander(
                f"👤 {name}（提出: {req.get('submitted_at', '')}）"
                f"　出勤希望: {work_days}日 / 希望OFF: {off_days}日"
            ):
                st.markdown(f"**CoCoスペ:** {spec_html}", unsafe_allow_html=True)
                st.markdown(f"**誕生日:** {ud.get('birthday', '') or '未設定'}")
                st.divider()
                for dk in sorted(entries.keys()):
                    e = entries[dk]
                    d = datetime.strptime(dk, "%Y-%m-%d").date()
                    wd2 = WEEKDAY_JP[d.weekday()]
                    if e.get("type") == "work":
                        note_txt = f"　{e['note']}" if e.get("note") else ""
                        st.write(f"　🟢 **{d.month}/{d.day}({wd2})** "
                                 f"{e.get('start','')}〜{e.get('end','')}{note_txt}")
                    elif e.get("type") == "off":
                        note_txt = f"　({e['note']})" if e.get("note") else ""
                        st.write(f"　🔴 **{d.month}/{d.day}({wd2})** 希望OFF{note_txt}")

                if st.button(f"📋 {name}の申請をシフトに一括反映", key=f"apply_{uname}"):
                    applied = 0
                    for dk, e in entries.items():
                        if e.get("type") == "work":
                            sc = get_shift_schedule(dk)
                            if "shifts" not in sc:
                                sc["shifts"] = {}
                            sc["shifts"][uname] = {
                                "periods": [[e.get("start", "09:00"), e.get("end", "17:00")]],
                                "note":    e.get("note", ""),
                            }
                            save_shift_schedule(dk, sc)
                            applied += 1
                    st.success(f"✅ {name}の申請を {applied} 日分反映しました。")

# ─── 設定 ──────────────────────────────────────────────────────
with tab_cfg:
    st.markdown("#### 申請締切日の管理")

    month_list2 = []
    for i in range(0, 4):
        d = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        month_list2.append(d.strftime("%Y-%m"))

    sel_m2 = st.selectbox("月を選択", month_list2,
                           format_func=lambda m: f"{m[:4]}年{int(m[5:7])}月",
                           key="cfg_month")
    cur_dl = get_shift_deadline(sel_m2)
    st.write(f"現在の締切日: **{cur_dl}**")

    try:
        dl_default = date.fromisoformat(cur_dl)
    except Exception:
        dl_default = today

    new_dl = st.date_input("新しい締切日", value=dl_default, key="new_dl")
    if st.button("締切日を更新", type="primary", key="upd_dl"):
        set_shift_deadline(sel_m2, new_dl.strftime("%Y-%m-%d"))
        st.success(f"✅ {sel_m2} の締切日を {new_dl} に更新しました。")
        st.rerun()

    st.divider()
    st.markdown("#### 色の凡例")
    st.markdown(
        "<div style='display:flex;flex-direction:column;gap:10px;margin-top:8px;'>"
        "<div style='display:flex;align-items:center;gap:12px;'>"
        "<div style='width:40px;height:24px;background:#5b4b97;border-radius:4px;'></div>"
        "<span>バイト（アルバイト）</span></div>"
        "<div style='display:flex;align-items:center;gap:12px;'>"
        "<div style='width:40px;height:24px;background:#1e6ab5;border-radius:4px;'></div>"
        "<span>社員</span></div>"
        "<div style='display:flex;align-items:center;gap:12px;'>"
        "<div style='width:40px;height:24px;border-bottom:3px solid #dc3545;'></div>"
        "<span>人員不足（最低必要人員を下回る時間帯）</span></div>"
        "</div>",
        unsafe_allow_html=True,
    )
