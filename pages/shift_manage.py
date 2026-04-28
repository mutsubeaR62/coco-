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

# ─── シフト確認 ────────────────────────────────────────────────
with tab_view:
    sel_date = st.date_input("日付を選択", value=today, key="view_date")
    date_str = sel_date.strftime("%Y-%m-%d")
    wd = WEEKDAY_JP[sel_date.weekday()]
    day_color = "color:#dc3545;" if sel_date.weekday() == 6 else (
        "color:#1e6ab5;" if sel_date.weekday() == 5 else "")
    st.markdown(
        f"<h4 style='{day_color}'>{sel_date.year}年{sel_date.month}月{sel_date.day}日（{wd}）</h4>",
        unsafe_allow_html=True,
    )

    schedule = get_shift_schedule(date_str)

    # 売上目標・最低人員の設定
    with st.expander("⚙️ この日の設定", expanded=False):
        cs1, cs2 = st.columns(2)
        new_target = cs1.number_input("売上目標 (¥)", value=int(schedule.get("sales_target", 0)),
                                       step=1000, min_value=0, key="tgt")
        new_min = cs2.number_input("最低必要人員（人）", value=int(schedule.get("min_staff", 3)),
                                    step=1, min_value=1, key="minst")
        if st.button("保存", key="save_cfg"):
            schedule["sales_target"] = new_target
            schedule["min_staff"] = new_min
            save_shift_schedule(date_str, schedule)
            st.success("設定を保存しました")
            st.rerun()

    render_grid(schedule, users_dict)

    st.divider()
    st.markdown("#### シフトを追加 / 編集")

    user_opts = {u["name"]: u["username"] for u in all_users}
    sel_name  = st.selectbox("スタッフを選択", list(user_opts.keys()), key="add_sel")
    sel_uname = user_opts[sel_name]

    # 現在のシフトデータ取得（常に最新）
    sc_now    = get_shift_schedule(date_str)
    ex_shift  = sc_now.get("shifts", {}).get(sel_uname, {})
    periods   = get_periods(ex_shift)

    # ── 現在の勤務時間帯 ──────────────────────────────────────
    if periods:
        st.markdown("**現在の勤務時間帯**")
        for i, (ps, pe) in enumerate(periods):
            c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
            with c1:
                ns = st.selectbox("開始", TIME_OPTS,
                                   index=TIME_OPTS.index(ps) if ps in TIME_OPTS else 0,
                                   key=f"ps_{sel_uname}_{i}")
            with c2:
                ne = st.selectbox("終了", TIME_OPTS,
                                   index=TIME_OPTS.index(pe) if pe in TIME_OPTS else 0,
                                   key=f"pe_{sel_uname}_{i}")
            with c3:
                if st.button("💾 更新", key=f"upd_p_{sel_uname}_{i}"):
                    new_p = [p[:] for p in periods]
                    new_p[i] = [ns, ne]
                    sc_now["shifts"][sel_uname]["periods"] = new_p
                    sc_now["shifts"][sel_uname].pop("start", None)
                    sc_now["shifts"][sel_uname].pop("end", None)
                    save_shift_schedule(date_str, sc_now)
                    st.rerun()
            with c4:
                if st.button("🗑️", key=f"del_p_{sel_uname}_{i}", help="この時間帯を削除"):
                    new_p = [p for j, p in enumerate(periods) if j != i]
                    if new_p:
                        sc_now["shifts"].setdefault(sel_uname, {})["periods"] = new_p
                        sc_now["shifts"][sel_uname].pop("start", None)
                        sc_now["shifts"][sel_uname].pop("end", None)
                    else:
                        sc_now.get("shifts", {}).pop(sel_uname, None)
                    save_shift_schedule(date_str, sc_now)
                    st.rerun()
    else:
        st.caption("まだシフトが登録されていません。")

    # ── 時間帯を追加 ─────────────────────────────────────────
    st.markdown("**時間帯を追加**")
    ca, cb, cc = st.columns([2, 2, 2])
    with ca:
        add_start = st.selectbox("開始", TIME_OPTS,
                                  index=TIME_OPTS.index("09:00"), key="add_ps")
    with cb:
        add_end = st.selectbox("終了", TIME_OPTS,
                                index=TIME_OPTS.index("17:00"), key="add_pe")
    with cc:
        add_note = st.text_input("備考", value=ex_shift.get("note", ""),
                                  placeholder="例: 22時30分まで", key="add_note")

    col_add, col_del = st.columns(2)
    if col_add.button("＋ 追加", type="primary", key="do_add"):
        sc_now2 = get_shift_schedule(date_str)
        if "shifts" not in sc_now2:
            sc_now2["shifts"] = {}
        ex2 = sc_now2["shifts"].get(sel_uname, {})
        new_p = get_periods(ex2) + [[add_start, add_end]]
        sc_now2["shifts"][sel_uname] = {
            "periods": new_p,
            "note": add_note,
        }
        save_shift_schedule(date_str, sc_now2)
        st.success(f"✅ {sel_name} に {add_start}〜{add_end} を追加しました。")
        st.rerun()

    if col_del.button("🗑️ このスタッフをシフトから削除", key="do_del"):
        sc_now2 = get_shift_schedule(date_str)
        sc_now2.get("shifts", {}).pop(sel_uname, None)
        save_shift_schedule(date_str, sc_now2)
        st.warning(f"{sel_name} のシフトを削除しました。")
        st.rerun()

    # 備考だけ更新するボタン
    if periods and st.button("📝 備考を保存", key="save_note"):
        sc_now2 = get_shift_schedule(date_str)
        sc_now2["shifts"].setdefault(sel_uname, {})["note"] = add_note
        save_shift_schedule(date_str, sc_now2)
        st.success("備考を保存しました。")
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
