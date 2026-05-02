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

SHIFT_TYPES = ["自店舗", "レギュラー", "欠員", "地店舗ヘルプ", "発注", "ごみ捨て"]
TYPE_COLORS = {
    "自店舗":       "#5b4b97",
    "レギュラー":   "#1e6ab5",
    "欠員":         "#dc3545",
    "地店舗ヘルプ": "#e83e8c",
    "発注":         "#f48c06",
    "ごみ捨て":     "#28a745",
}

# 30分刻みスロット 9:00〜24:00
HALF_SLOTS = [(h, m) for h in range(9, 24) for m in (0, 30)]
TIME_OPTS   = [f"{h:02d}:{m:02d}" for h in range(8, 25) for m in (0, 30)]


# ─── ヘルパー ──────────────────────────────────────────────────
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


# ─── グリッド表示 ─────────────────────────────────────────────
def render_shift_grid(schedule, users_dict, date_str=None):
    shifts       = schedule.get("shifts", {})
    memo         = schedule.get("memo", "")
    min_staff    = int(schedule.get("min_staff", 3))
    sales_target = float(schedule.get("sales_target", 0))

    # 人件費・人員数計算
    total_labor    = 0.0
    count_per_slot = {(h, m): 0 for h, m in HALF_SLOTS}
    for uname, si in shifts.items():
        ud   = users_dict.get(uname, {})
        wage = float(ud.get("hourly_wage", 1050))
        pds  = get_periods(si)
        total_labor += calc_hours(pds) * wage
        for h, m in HALF_SLOTS:
            if slot_in_periods(pds, h, m):
                count_per_slot[(h, m)] += 1

    ratio = (total_labor / sales_target * 100) if sales_target > 0 else None

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("売上目標",    f"¥{sales_target:,.0f}")
    mc2.metric("人件費見込み", f"¥{total_labor:,.0f}")
    mc3.metric("人件費率",    f"{ratio:.1f}%" if ratio is not None else "—")

    if memo:
        st.info(f"📝 **メモ:** {memo}")

    if not shifts:
        st.info("この日のシフトはまだ登録されていません。")
        return

    # 凡例
    leg = "<div style='display:flex;flex-wrap:wrap;gap:6px;margin:6px 0 10px;font-size:12px;'>"
    for t, c in TYPE_COLORS.items():
        leg += f"<span style='background:{c};color:#fff;padding:2px 9px;border-radius:4px;'>{t}</span>"
    leg += "</div>"
    st.markdown(leg, unsafe_allow_html=True)

    # HTML テーブル（30分刻み）
    tbl = """
<style>
.s30{border-collapse:collapse;font-size:12px;width:100%;}
.s30 th,.s30 td{border:1px solid #e8e8e8;padding:4px 0;text-align:center;white-space:nowrap;color:#333;}
.s30 .nc{text-align:left;min-width:80px;font-weight:600;background:#fafafa;padding:4px 8px;color:#222;}
.s30 .ac{text-align:left;min-width:70px;font-size:11px;color:#666;background:#fafafa;padding:4px 5px;}
.s30 .hh{min-width:14px;width:14px;}
.s30 .tw{min-width:34px;font-weight:600;color:#444;}
.s30 .oh{border-left:1px solid #bbb!important;}
.s30 thead th{background:#f5f5f5;font-weight:600;color:#555;font-size:11px;}
.s30 .low{color:#dc3545;font-weight:700;}
</style>
<div style="overflow-x:auto;"><table class="s30"><thead><tr>
<th class="nc">名前</th><th class="ac">備考</th>
"""
    for h in range(9, 24):
        tbl += f'<th class="oh" colspan="2">{h}</th>'
    tbl += '<th class="tw">時間</th></tr></thead><tbody>'

    sorted_shifts = sorted(
        shifts.items(),
        key=lambda x: (
            0 if get_employee_type(users_dict.get(x[0], {})) == "seishain" else 1,
            users_dict.get(x[0], {}).get("name", x[0]),
        ),
    )

    for uname, si in sorted_shifts:
        ud    = users_dict.get(uname, {})
        name  = ud.get("name", uname)
        note  = si.get("note", "")
        stype = si.get("type", "自店舗")
        color = TYPE_COLORS.get(stype, "#5b4b97")
        pds   = get_periods(si)
        hrs   = calc_hours(pds)
        tbl  += f'<tr><td class="nc">{name}</td><td class="ac">{note}</td>'
        for h, m in HALF_SLOTS:
            cls = "hh oh" if m == 0 else "hh"
            if slot_in_periods(pds, h, m):
                tbl += f'<td class="{cls}" style="background:{color}"></td>'
            else:
                tbl += f'<td class="{cls}"></td>'
        tbl += f'<td class="tw">{hrs:.1f}</td></tr>'

    # 人員数行
    tbl += '<tr style="border-top:2px solid #999;"><td class="nc" colspan="2" style="font-weight:700;color:#666;">人員数</td>'
    for h, m in HALF_SLOTS:
        c   = count_per_slot[(h, m)]
        cls = "hh oh" if m == 0 else "hh"
        if 0 < c < min_staff:
            tbl += f'<td class="{cls} low">{c}</td>'
        else:
            tbl += f'<td class="{cls}">{c if c else ""}</td>'
    tbl += '<td class="tw"></td></tr></tbody></table></div>'

    st.markdown(tbl, unsafe_allow_html=True)

    # LINE用画像エクスポート
    if date_str:
        if st.button("📷 LINE用画像を生成", key=f"exp_{date_str}"):
            img_bytes = _generate_image(date_str, schedule, users_dict,
                                        sorted_shifts, count_per_slot,
                                        total_labor, ratio)
            if img_bytes:
                st.download_button(
                    "⬇️ 画像をダウンロード",
                    data=img_bytes,
                    file_name=f"shift_{date_str}.png",
                    mime="image/png",
                    key=f"dl_{date_str}",
                )


def _generate_image(date_str, schedule, users_dict,
                    sorted_shifts, count_per_slot, total_labor, ratio):
    try:
        from PIL import Image, ImageDraw, ImageFont
        import io

        sales_target = float(schedule.get("sales_target", 0))
        min_staff    = int(schedule.get("min_staff", 3))
        memo         = schedule.get("memo", "")

        # フォント
        font_candidates = [
            "C:/Windows/Fonts/meiryo.ttc",
            "C:/Windows/Fonts/YuGothM.ttc",
            "C:/Windows/Fonts/msgothic.ttc",
        ]
        fnt = fsm = fbold = None
        for fp in font_candidates:
            if os.path.exists(fp):
                try:
                    fnt   = ImageFont.truetype(fp, 12)
                    fsm   = ImageFont.truetype(fp, 10)
                    fbold = ImageFont.truetype(fp, 13)
                    break
                except Exception:
                    pass
        if fnt is None:
            fnt = fsm = fbold = ImageFont.load_default()

        NW, NOTEW, SW, TW, RH = 90, 80, 13, 38, 20
        PAD, LW = 10, 130
        ns = len(HALF_SLOTS)

        grid_w   = NW + NOTEW + ns * SW + TW
        total_w  = PAD + grid_w + PAD + LW + PAD
        hdr_h    = 55
        col_h    = RH
        body_h   = (len(sorted_shifts) + 1) * RH
        memo_h   = 36 if memo else 0
        total_h  = PAD + hdr_h + col_h + body_h + memo_h + PAD

        img  = Image.new("RGB", (total_w, total_h), "white")
        draw = ImageDraw.Draw(img)

        def hex2rgb(h):
            return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))

        # ヘッダー
        d_obj = date.fromisoformat(date_str)
        wd    = WEEKDAY_JP[d_obj.weekday()]
        draw.text((PAD, PAD),
                  f"{d_obj.year}年{d_obj.month}月{d_obj.day}日（{wd}）",
                  fill="#222", font=fbold)
        y2 = PAD + 18
        draw.text((PAD,        y2), f"売上目標: ¥{sales_target:,.0f}",     fill="#555", font=fsm)
        draw.text((PAD + 170,  y2), f"人件費: ¥{total_labor:,.0f}",        fill="#555", font=fsm)
        draw.text((PAD + 340,  y2), f"人件費率: {ratio:.1f}%" if ratio else "人件費率: —", fill="#555", font=fsm)

        # グリッド Y 開始
        gy = PAD + hdr_h
        gx = PAD

        # 列ヘッダー行
        draw.rectangle([gx, gy, gx + NW, gy + RH], fill="#e8e8e8", outline="#bbb")
        draw.text((gx + 3, gy + 4), "名前", fill="#333", font=fsm)
        draw.rectangle([gx + NW, gy, gx + NW + NOTEW, gy + RH], fill="#e8e8e8", outline="#bbb")
        draw.text((gx + NW + 3, gy + 4), "備考", fill="#333", font=fsm)
        for i, (h, m) in enumerate(HALF_SLOTS):
            x    = gx + NW + NOTEW + i * SW
            fill = "#d8d8d8" if m == 0 else "#e8e8e8"
            draw.rectangle([x, gy, x + SW, gy + RH], fill=fill, outline="#bbb")
            if m == 0:
                draw.text((x + 1, gy + 4), str(h), fill="#333", font=fsm)
        tw_x = gx + NW + NOTEW + ns * SW
        draw.rectangle([tw_x, gy, tw_x + TW, gy + RH], fill="#e8e8e8", outline="#bbb")
        draw.text((tw_x + 4, gy + 4), "時間", fill="#333", font=fsm)
        gy += RH

        # スタッフ行
        for uname, si in sorted_shifts:
            ud    = users_dict.get(uname, {})
            name  = ud.get("name", uname)
            note  = si.get("note", "")
            stype = si.get("type", "自店舗")
            rgb   = hex2rgb(TYPE_COLORS.get(stype, "#5b4b97"))
            pds   = get_periods(si)
            hrs   = calc_hours(pds)

            draw.rectangle([gx, gy, gx + NW, gy + RH], fill="white", outline="#ccc")
            draw.text((gx + 3, gy + 4), name[:10], fill="#222", font=fnt)
            draw.rectangle([gx + NW, gy, gx + NW + NOTEW, gy + RH], fill="white", outline="#ccc")
            draw.text((gx + NW + 3, gy + 4), note[:10], fill="#555", font=fsm)

            for i, (h, m) in enumerate(HALF_SLOTS):
                x   = gx + NW + NOTEW + i * SW
                out = "#888" if m == 0 else "#ccc"
                if slot_in_periods(pds, h, m):
                    draw.rectangle([x, gy, x + SW, gy + RH], fill=rgb, outline=out)
                else:
                    draw.rectangle([x, gy, x + SW, gy + RH], fill="white", outline=out)

            draw.rectangle([tw_x, gy, tw_x + TW, gy + RH], fill="white", outline="#ccc")
            draw.text((tw_x + 4, gy + 4), f"{hrs:.1f}", fill="#222", font=fnt)
            gy += RH

        # 人員数行
        draw.rectangle([gx, gy, gx + NW + NOTEW, gy + RH], fill="#f5f5f5", outline="#bbb")
        draw.text((gx + 4, gy + 4), "人員数", fill="#666", font=fsm)
        for i, (h, m) in enumerate(HALF_SLOTS):
            x   = gx + NW + NOTEW + i * SW
            c   = count_per_slot.get((h, m), 0)
            out = "#888" if m == 0 else "#ccc"
            bg  = "#fff0f0" if 0 < c < min_staff else "#f5f5f5"
            draw.rectangle([x, gy, x + SW, gy + RH], fill=bg, outline=out)
            if c > 0:
                col = "#dc3545" if 0 < c < min_staff else "#333"
                draw.text((x + 2, gy + 4), str(c), fill=col, font=fsm)
        draw.rectangle([tw_x, gy, tw_x + TW, gy + RH], fill="#f5f5f5", outline="#bbb")
        gy += RH

        # メモ
        if memo:
            draw.rectangle([gx, gy + 4, gx + grid_w, gy + memo_h - 4],
                           fill="#fffdf0", outline="#f48c06")
            draw.text((gx + 8, gy + 12), f"メモ: {memo}", fill="#555", font=fnt)

        # 凡例
        lx = PAD + grid_w + PAD
        draw.text((lx, PAD), "凡例", fill="#333", font=fbold)
        for i, (t, c) in enumerate(TYPE_COLORS.items()):
            ly = PAD + 20 + i * 22
            draw.rectangle([lx, ly, lx + 18, ly + 14], fill=hex2rgb(c), outline="#aaa")
            draw.text((lx + 24, ly), t, fill="#333", font=fsm)

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf.getvalue()

    except Exception as e:
        st.error(f"画像生成エラー: {e}")
        return None


# ═══ タブ ══════════════════════════════════════════════════════
tab_view, tab_req, tab_cfg = st.tabs(["📊 シフト確認・編集", "📥 申請管理", "⚙️ 設定"])

all_users   = get_all_users()
users_dict  = {u["username"]: u for u in all_users}

# ─── シフト確認 & 編集 ────────────────────────────────────────
with tab_view:
    month_opts = []
    for i in range(-1, 4):
        d = (today.replace(day=1) + timedelta(days=32 * i)).replace(day=1)
        month_opts.append(d.strftime("%Y-%m"))
    sel_month = st.selectbox(
        "月を選択", month_opts, index=1,
        format_func=lambda m: f"{m[:4]}年{int(m[5:7])}月",
        key="view_month_mgr",
    )
    y_m, m_m   = int(sel_month[:4]), int(sel_month[5:7])
    num_days_m = calendar.monthrange(y_m, m_m)[1]

    all_requests_m = get_all_shift_requests(sel_month)

    # 月合計人件費
    total_labor_m = 0.0
    for day_num in range(1, num_days_m + 1):
        sc_tmp = get_shift_schedule(date(y_m, m_m, day_num).strftime("%Y-%m-%d"))
        for uname_t, si_t in sc_tmp.get("shifts", {}).items():
            ud_t = users_dict.get(uname_t, {})
            total_labor_m += calc_hours(get_periods(si_t)) * float(ud_t.get("hourly_wage", 1050))
    st.metric("今月の人件費合計（概算）", f"¥{total_labor_m:,.0f}")
    st.divider()

    for day_num in range(1, num_days_m + 1):
        d   = date(y_m, m_m, day_num)
        ds  = d.strftime("%Y-%m-%d")
        wd  = WEEKDAY_JP[d.weekday()]
        dc  = "color:#dc3545;" if d.weekday() == 6 else (
              "color:#1e6ab5;" if d.weekday() == 5 else "color:#333;")

        schedule_d = get_shift_schedule(ds)
        shifts_d   = schedule_d.get("shifts", {})

        st.markdown(
            f"<div style='font-size:1.05rem;font-weight:700;{dc}"
            f"padding:6px 0 2px;border-bottom:2px solid #eee;margin-top:12px;'>"
            f"{m_m}/{day_num}（{wd}）</div>",
            unsafe_allow_html=True,
        )

        if shifts_d:
            render_shift_grid(schedule_d, users_dict, date_str=ds)
        else:
            st.caption("— 未登録 —")

        with st.expander(f"✏️ {m_m}/{day_num} を編集"):
            # ─ 基本設定 ─
            cs1, cs2 = st.columns(2)
            new_target = cs1.number_input("売上目標 (¥)", value=int(schedule_d.get("sales_target", 0)),
                                           step=1000, min_value=0, key=f"tgt_{ds}")
            new_min    = cs2.number_input("最低必要人員", value=int(schedule_d.get("min_staff", 3)),
                                           step=1, min_value=1, key=f"minst_{ds}")
            new_memo   = st.text_input("📝 メモ（イベント情報など）",
                                        value=schedule_d.get("memo", ""),
                                        placeholder="例: 〇〇フェア、育成引き続き",
                                        key=f"memo_{ds}")
            st.divider()

            # ─ スタッフシフト入力 ─
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

            # 追加するスタッフを選択
            existing_names = {users_dict.get(u, {}).get("name", u): u for u in target_unames}
            all_names      = {u_data["name"]: u_data["username"] for u_data in all_users}
            extra_names    = [n for n in all_names if n not in existing_names]
            add_sel = st.multiselect("＋ スタッフを追加", extra_names, key=f"add_{ds}")
            for n in add_sel:
                uname = all_names[n]
                if uname not in target_unames:
                    target_unames.append(uname)

            if not target_unames:
                st.caption("申請・登録済みのスタッフがいません。")
            else:
                st.markdown(
                    "<div style='display:flex;gap:0;margin-bottom:4px;font-size:0.78rem;color:#888;'>"
                    "<span style='flex:2;'>名前</span>"
                    "<span style='flex:2;'>種別</span>"
                    "<span style='flex:1.5;'>開始</span>"
                    "<span style='flex:1.5;'>終了</span>"
                    "<span style='flex:2;'>備考</span>"
                    "<span style='flex:0.5;'></span>"
                    "</div>",
                    unsafe_allow_html=True,
                )

                new_shifts = dict(shifts_d)  # コピーして編集
                to_remove  = []

                for uname in target_unames:
                    ud   = users_dict.get(uname, {})
                    name = ud.get("name", uname)
                    si   = shifts_d.get(uname, {})
                    pds  = get_periods(si)
                    if not pds and uname in req_for_day:
                        e   = req_for_day[uname]
                        pds = [[e.get("start", "09:00"), e.get("end", "17:00")]]

                    def_type  = si.get("type", "自店舗")
                    def_start = pds[0][0] if pds else "09:00"
                    def_end   = pds[0][1] if pds else "17:00"
                    def_note  = si.get("note", "") or req_for_day.get(uname, {}).get("note", "")

                    c_name, c_type, c_start, c_end, c_note, c_del = st.columns([2, 2, 1.5, 1.5, 2, 0.5])
                    with c_name:
                        color = TYPE_COLORS.get(def_type, "#5b4b97")
                        st.markdown(
                            f"<div style='padding:8px 4px;font-weight:600;'>"
                            f"<span style='display:inline-block;width:10px;height:10px;"
                            f"background:{color};border-radius:50%;margin-right:6px;'></span>"
                            f"{name}</div>",
                            unsafe_allow_html=True,
                        )
                    with c_type:
                        s_type = st.selectbox("種別", SHIFT_TYPES,
                            index=SHIFT_TYPES.index(def_type) if def_type in SHIFT_TYPES else 0,
                            key=f"stype_{ds}_{uname}", label_visibility="collapsed")
                    with c_start:
                        s_start = st.selectbox("開始", TIME_OPTS,
                            index=TIME_OPTS.index(def_start) if def_start in TIME_OPTS else 2,
                            key=f"start_{ds}_{uname}", label_visibility="collapsed")
                    with c_end:
                        s_end = st.selectbox("終了", TIME_OPTS,
                            index=TIME_OPTS.index(def_end) if def_end in TIME_OPTS else 18,
                            key=f"end_{ds}_{uname}", label_visibility="collapsed")
                    with c_note:
                        s_note = st.text_input("備考", value=def_note,
                            key=f"snote_{ds}_{uname}", label_visibility="collapsed")
                    with c_del:
                        if st.button("🗑", key=f"del_{ds}_{uname}", help="このシフトを削除"):
                            to_remove.append(uname)

                    new_shifts[uname] = {
                        "periods": [[s_start, s_end]],
                        "type":    s_type,
                        "note":    s_note,
                    }

                for u in to_remove:
                    new_shifts.pop(u, None)

                if st.button("💾 シフトを保存", type="primary", key=f"save_{ds}"):
                    sc_save = {
                        "sales_target": new_target,
                        "min_staff":    new_min,
                        "memo":         new_memo,
                        "shifts":       {k: v for k, v in new_shifts.items() if k not in to_remove},
                    }
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

    sel_month_r = st.selectbox("月を選択", month_list,
                                format_func=lambda m: f"{m[:4]}年{int(m[5:7])}月",
                                index=1, key="req_month")
    dl = get_shift_deadline(sel_month_r)
    st.info(f"📅 申請締切: {dl}")

    requests = get_all_shift_requests(sel_month_r)
    if not requests:
        st.info("まだ申請がありません。")
    else:
        for uname, req in requests.items():
            ud        = users_dict.get(uname, {})
            name      = ud.get("name", uname)
            entries   = req.get("entries", {})
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
                    e   = entries[dk]
                    d   = datetime.strptime(dk, "%Y-%m-%d").date()
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
                            sc.setdefault("shifts", {})[uname] = {
                                "periods": [[e.get("start", "09:00"), e.get("end", "17:00")]],
                                "type":    "自店舗",
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
    leg2 = "<div style='display:flex;flex-direction:column;gap:10px;margin-top:8px;'>"
    for t, c in TYPE_COLORS.items():
        leg2 += (f"<div style='display:flex;align-items:center;gap:12px;'>"
                 f"<div style='width:40px;height:22px;background:{c};border-radius:4px;'></div>"
                 f"<span>{t}</span></div>")
    leg2 += "<div style='display:flex;align-items:center;gap:12px;'><div style='width:40px;height:22px;border-bottom:3px solid #dc3545;'></div><span>人員不足（最低必要人員を下回る時間帯）</span></div>"
    leg2 += "</div>"
    st.markdown(leg2, unsafe_allow_html=True)
