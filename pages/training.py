import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
import random
from utils import (apply_theme, require_login, page_header, get_progress, save_progress,
                   award_stamps, show_new_stamps, STAMPS, load_json, save_json,
                   get_all_users, ROLE_LABELS)

apply_theme()
require_login()

user = st.session_state.user
username = user["username"]
role = user.get("role", "kenshu")

# ─── 学習データ ───────────────────────────────────────────────
FLASHCARDS = [
    {"front": "辛さ 1辛",       "back": "ほんのり辛い。辛いものが苦手な方にも◎"},
    {"front": "辛さ 3辛",       "back": "標準的な辛さ。一番人気のレベル"},
    {"front": "辛さ 5辛〜",     "back": "⚠️ 辛さ確認必須！「かなり辛いですがよろしいですか？」"},
    {"front": "辛さ 10辛",      "back": "最高辛さ。唐辛子ベースの激辛"},
    {"front": "ライス 並",       "back": "300g（基本サイズ）"},
    {"front": "ライス 大",       "back": "400g"},
    {"front": "ライス 特大",     "back": "500g"},
    {"front": "ライス 少なめ",   "back": "200g（並より少ない）"},
    {"front": "福神漬け",        "back": "赤い漬物。無料で提供されるトッピング"},
    {"front": "らっきょう",      "back": "甘酸っぱい漬物。有料トッピング"},
    {"front": "ロースカツ",      "back": "豚ロース肉のカツ。定番人気トッピング"},
    {"front": "チキンカツ",      "back": "鶏むね肉のカツ。ロースよりあっさり"},
    {"front": "クリームコロッケ", "back": "クリーム入りのコロッケ。甘みとカレーが◎"},
    {"front": "「いらっしゃいませ」", "back": "お客様が入店されたときの第一声"},
    {"front": "「少々お待ちくださいませ」", "back": "お客様をお待たせするときの言葉"},
    {"front": "「ありがとうございました」", "back": "退店時・支払い後の感謝の言葉"},
    {"front": "HACCP",          "back": "食品衛生管理の国際基準。危害要因を事前に分析・管理"},
    {"front": "クロスコンタミネーション", "back": "食材の交差汚染。アレルゲンが別食材に混入すること"},
    {"front": "QSC",            "back": "Quality（品質）・Service（サービス）・Cleanliness（清潔）飲食業の3原則"},
    {"front": "冷蔵保存温度",    "back": "10℃以下"},
    {"front": "加熱調理の基準",  "back": "75℃以上・1分以上"},
    {"front": "手洗い所要時間",  "back": "石けんで20秒以上"},
]

QUIZ = [
    {
        "q": "辛さ5辛以上を注文されたとき、何をすべきですか？",
        "choices": ["そのまま通す", "辛さ確認をしてから通す", "店長に聞く", "断る"],
        "answer": 1,
        "exp": "5辛以上は「かなり辛いですがよろしいですか？」と確認。強く止めず、同意を得てから通します。"
    },
    {
        "q": "ライス「並」は何グラムですか？",
        "choices": ["200g", "250g", "300g", "400g"],
        "answer": 2,
        "exp": "並は300g。少なめ200g、大400g、特大500g、600g〜1000gの注文も可能です。"
    },
    {
        "q": "アレルギーの申告があったとき、正しい対応は？",
        "choices": ["自分で調べて答える", "「わかりません」と伝える", "必ず店長・社員に報告する", "メニュー表を渡す"],
        "answer": 2,
        "exp": "アレルギー対応は命にかかわります。自己判断は絶対NG。必ず店長・社員に報告してください。"
    },
    {
        "q": "正しい食器洗いの順番はどれですか？",
        "choices": ["油物→汚れ少ない→グラス", "グラス→汚れ少ない→油物", "何でもOK", "まず消毒してから洗う"],
        "answer": 1,
        "exp": "汚れの少ないものから洗うのが衛生的。グラス→普通の食器→油物の順がベストです。"
    },
    {
        "q": "お客様が入店されたとき、何と声かけしますか？",
        "choices": ["「はい」", "「いらっしゃいませ」", "「こんにちは」", "「どうぞ」"],
        "answer": 1,
        "exp": "「いらっしゃいませ」が基本。入店した瞬間に元気よく声をかけることが大切です。"
    },
    {
        "q": "クレームが発生したとき、まず何をすべきですか？",
        "choices": ["言い訳する", "店長を呼ぶ", "まず謝罪・傾聴する", "お客様に反論する"],
        "answer": 2,
        "exp": "まず「申し訳ございません」と誠意を示し、話を聞く。その後に店長へ報告します。"
    },
    {
        "q": "手洗いは石けんで何秒以上が必要ですか？",
        "choices": ["5秒以上", "10秒以上", "20秒以上", "30秒以上"],
        "answer": 2,
        "exp": "手洗いは石けんで20秒以上が基準。特に指の間・爪の中まで丁寧に洗いましょう。"
    },
    {
        "q": "冷蔵品の管理温度として正しいのはどれですか？",
        "choices": ["15℃以下", "10℃以下", "5℃以下", "0℃以下"],
        "answer": 1,
        "exp": "冷蔵品は10℃以下で管理。冷凍品は-18℃以下、加熱調理は75℃以上1分以上が基準です。"
    },
    {
        "q": "退店されるお客様への正しい挨拶はどれですか？",
        "choices": ["「はい」", "「ありがとうございます」", "「ありがとうございました。またお越しくださいませ」", "「お気をつけて」"],
        "answer": 2,
        "exp": "「ありがとうございました。またお越しくださいませ」が正解。最後の印象が次の来店につながります。"
    },
    {
        "q": "QSCとは何の略ですか？",
        "choices": ["Quick・Safe・Clean", "Quality・Service・Cleanliness", "Queue・Speed・Customer", "Quick・Smart・Careful"],
        "answer": 1,
        "exp": "QSC = Quality（品質）・Service（サービス）・Cleanliness（清潔）。飲食業の3原則です。"
    },
]

# ─── 卒業チェックリストテンプレート ──────────────────────────────
DEFAULT_GRADUATION_TEMPLATE = {
    "categories": [
        {
            "id": "service",
            "name": "接客",
            "items": [
                "入退店の挨拶ができる（いらっしゃいませ・ありがとうございました）",
                "注文を正確に受けて復唱確認できる",
                "5辛以上の辛さ確認ができる",
                "アレルギー対応の報告手順を知っている",
                "POSレジで注文入力・会計ができる",
            ]
        },
        {
            "id": "kitchen",
            "name": "調理・キッチン",
            "items": [
                "盛り付けの基本手順を知っている",
                "食材の保管場所と管理方法を知っている",
                "食器の洗い方（順番・グラス→食器→油物）を知っている",
            ]
        },
        {
            "id": "hygiene",
            "name": "衛生管理",
            "items": [
                "手洗いのタイミングと方法を知っている（石けんで20秒以上）",
                "身だしなみ基準を満たしている（爪・髪・アクセサリー）",
                "食品の温度管理基準を知っている（冷蔵10℃以下・加熱75℃以上）",
            ]
        },
        {
            "id": "operation",
            "name": "開閉店作業",
            "items": [
                "開店前チェックを一人でこなせる",
                "閉店作業チェックを一人でこなせる",
            ]
        },
        {
            "id": "knowledge",
            "name": "知識確認",
            "items": [
                "クイズで7問以上正解した（合格ライン）",
                "マニュアルを読んで基本ルールを理解している",
            ]
        },
    ]
}

def get_graduation_template():
    data = load_json("graduation_template.json", {})
    if not data.get("categories"):
        save_json("graduation_template.json", DEFAULT_GRADUATION_TEMPLATE)
        return DEFAULT_GRADUATION_TEMPLATE["categories"]
    return data["categories"]

def get_training_checks():
    return load_json("training_check.json", {})

def save_training_checks(data):
    save_json("training_check.json", data)

# セッション初期化
def init_session():
    defaults = {
        "fc_index": 0, "fc_show_back": False,
        "fc_order": list(range(len(FLASHCARDS))),
        "quiz_started": False, "quiz_finished": False,
        "quiz_index": 0, "quiz_score": 0,
        "quiz_answers": [], "quiz_order": list(range(len(QUIZ))),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()
progress = get_progress(username)
earned_stamps = set(progress.get("stamps", []))

page_header("🎓 新人研修", "フラッシュカード・クイズ・スタンプで楽しく覚えよう！")

# ══════════════════════════════════════════════════════════════
# 研修以外のロール → 卒業チェックリスト管理ビュー
# ══════════════════════════════════════════════════════════════
if role != "kenshu":
    all_users = get_all_users()
    kenshu_users = [u for u in all_users if u.get("role") == "kenshu"]

    if not kenshu_users:
        st.info("現在、研修中のメンバーはいません。")
        st.stop()

    categories = get_graduation_template()
    training_data = get_training_checks()
    is_mgr = role in ("admin", "daiko")
    total_items = sum(len(cat["items"]) for cat in categories)

    st.markdown("### 研修生の卒業チェック")
    st.caption("各項目ができていたらチェックを入れてください。自動保存されます。")

    for ku in kenshu_users:
        kun   = ku["username"]
        kname = ku["name"]
        prog  = get_progress(kun)
        quiz_scores  = prog.get("quiz_scores", [])
        cl_done      = prog.get("checklist_completions", {})

        checks = training_data.get(kun, {})
        done_count = sum(
            1 for cat in categories for item in cat["items"]
            if checks.get(f"{cat['name']}::{item}", False)
        )
        remaining = total_items - done_count
        pct = int(done_count / total_items * 100) if total_items > 0 else 0
        is_ready = (done_count == total_items)

        status_label = "卒業準備完了！" if is_ready else f"あと {remaining} 項目"

        with st.expander(
            f"{kname}　　{done_count}/{total_items} 完了 — {status_label}",
            expanded=True,
        ):
            # 進捗バー
            st.progress(pct / 100)

            # スタッツ
            c1, c2, c3 = st.columns(3)
            c1.metric("クイズ最高点",
                      f"{max(quiz_scores)}/10" if quiz_scores else "未受験")
            c2.metric("チェックリスト完了", f"{sum(cl_done.values())}回")
            c3.metric("残り項目", f"{remaining} 項目")

            st.divider()

            changed = False
            new_checks = dict(checks)

            # カテゴリ別チェック
            for cat in categories:
                cat_name = cat["name"]
                items    = cat["items"]
                cat_done = sum(1 for item in items
                               if checks.get(f"{cat_name}::{item}", False))
                all_cat_done = (cat_done == len(items))

                st.markdown(
                    f"**{'✅ ' if all_cat_done else ''}{cat_name}** "
                    f"<span style='color:#999;font-size:0.85rem;'>"
                    f"{cat_done}/{len(items)}</span>",
                    unsafe_allow_html=True,
                )

                for item in items:
                    key = f"{cat_name}::{item}"
                    cur_val = checks.get(key, False)
                    if is_mgr:
                        new_val = st.checkbox(
                            item, value=cur_val,
                            key=f"tr_{kun}_{key}",
                        )
                        if new_val != cur_val:
                            new_checks[key] = new_val
                            changed = True
                    else:
                        icon = "✅" if cur_val else "☐"
                        st.markdown(
                            f"<div style='padding:2px 0;color:{'#999' if not cur_val else '#222'};'>"
                            f"{icon} {item}</div>",
                            unsafe_allow_html=True,
                        )

                st.write("")

            if changed:
                training_data[kun] = new_checks
                save_training_checks(training_data)
                st.rerun()

            # 管理者メモ
            if is_mgr:
                st.divider()
                memo_key = f"memo_{kun}"
                cur_memo = training_data.get(memo_key, "")
                new_memo = st.text_area(
                    "メモ（管理者のみ表示）", value=cur_memo,
                    key=f"memo_area_{kun}", height=60,
                )
                if new_memo != cur_memo:
                    training_data[memo_key] = new_memo
                    save_training_checks(training_data)

    # テンプレート管理（管理者のみ）
    if role == "admin":
        st.divider()
        with st.expander("卒業チェックリストの項目編集（管理者）"):
            st.caption("研修卒業に必要な項目を管理します。変更は全研修生に即時反映されます。")

            # エディタ用スタイル
            st.markdown("""
<style>
.cat-header {
    background: linear-gradient(90deg, #fff3ee, #fff);
    border-left: 5px solid #e85d04;
    padding: 10px 16px;
    border-radius: 0 10px 10px 0;
    margin: 20px 0 6px;
}
.cat-header span {
    font-size: 0.72rem;
    font-weight: 700;
    color: #e85d04;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.items-label {
    font-size: 0.75rem;
    color: #888;
    font-weight: 600;
    margin: 10px 0 4px 4px;
}
.new-cat-section {
    background: #f8f9fa;
    border: 2px dashed #dee2e6;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)

            tmpl = load_json("graduation_template.json", DEFAULT_GRADUATION_TEMPLATE)
            cats = tmpl.get("categories", DEFAULT_GRADUATION_TEMPLATE["categories"])

            def _clear_tmpl_state(from_ci=0, from_ii=0, num_cats=50, max_items=50):
                """削除によってずれるウィジェットのセッションステートをクリアする"""
                for cj in range(from_ci, num_cats):
                    if f"catname_{cj}" in st.session_state:
                        del st.session_state[f"catname_{cj}"]
                    start_ii = from_ii if cj == from_ci else 0
                    for jj in range(start_ii, max_items):
                        for prefix in (f"tmpl_{cj}_{jj}", f"tmpl_del_{cj}_{jj}"):
                            if prefix in st.session_state:
                                del st.session_state[prefix]
                    if f"tmpl_add_{cj}" in st.session_state:
                        del st.session_state[f"tmpl_add_{cj}"]

            for ci, cat in enumerate(cats):
                # ─ カテゴリヘッダー ─────────────────────────────
                st.markdown(
                    f'<div class="cat-header"><span>カテゴリ {ci + 1}</span></div>',
                    unsafe_allow_html=True,
                )
                col_name, col_del = st.columns([10, 1])
                with col_name:
                    new_cat_name = st.text_input(
                        "カテゴリ名", value=cat["name"],
                        key=f"catname_{ci}",
                    )
                with col_del:
                    st.write("")
                    if st.button("🗑️", key=f"cat_del_{ci}",
                                 help="このカテゴリごと削除"):
                        num_cats_before = len(cats)
                        cats.pop(ci)
                        save_json("graduation_template.json", {"categories": cats})
                        _clear_tmpl_state(from_ci=ci, num_cats=num_cats_before)
                        st.rerun()

                # ─ チェック項目 ──────────────────────────────────
                st.markdown('<div class="items-label">チェック項目</div>',
                            unsafe_allow_html=True)

                new_items = []
                for ii, item in enumerate(cat["items"]):
                    # 字下げ用スペーサー列
                    _, col1, col2 = st.columns([0.3, 10.7, 1])
                    with col1:
                        new_item = st.text_input(
                            "", value=item,
                            key=f"tmpl_{ci}_{ii}",
                            label_visibility="collapsed",
                        )
                    with col2:
                        if st.button("🗑️", key=f"tmpl_del_{ci}_{ii}"):
                            original_len = len(cats[ci]["items"])
                            cats[ci]["items"].pop(ii)
                            save_json("graduation_template.json", {"categories": cats})
                            # 削除した位置以降のセッションステートをクリア
                            _clear_tmpl_state(from_ci=ci, from_ii=ii,
                                              num_cats=ci + 1, max_items=original_len)
                            st.rerun()
                    new_items.append(new_item)

                # 項目追加行
                _, col_add = st.columns([0.3, 11.7])
                with col_add:
                    add_item = st.text_input(
                        "", placeholder="＋ 項目を追加（入力してEnter）",
                        key=f"tmpl_add_{ci}",
                        label_visibility="collapsed",
                    )
                if add_item:
                    new_items.append(add_item)

                cats[ci]["name"]  = new_cat_name
                cats[ci]["items"] = new_items

            # ─ カテゴリ新規追加 ──────────────────────────────────
            st.markdown('<div class="new-cat-section">', unsafe_allow_html=True)
            new_cat_input = st.text_input(
                "カテゴリを追加",
                placeholder="新しいカテゴリ名を入力して Enter",
                key="tmpl_new_cat",
            )
            st.markdown('</div>', unsafe_allow_html=True)
            if new_cat_input:
                import uuid
                cats.append({"id": uuid.uuid4().hex[:8], "name": new_cat_input, "items": []})
                save_json("graduation_template.json", {"categories": cats})
                st.rerun()

            st.write("")
            if st.button("変更を保存", type="primary", key="save_tmpl"):
                save_json("graduation_template.json", {"categories": cats})
                st.success("保存しました！")
                st.rerun()

    st.stop()

# ══════════════════════════════════════════════════════════════
# 研修ロール → 卒業進捗 + 学習コンテンツ
# ══════════════════════════════════════════════════════════════

# 卒業進捗を上部に表示
_grad_cats   = get_graduation_template()
_grad_total  = sum(len(c["items"]) for c in _grad_cats)
_grad_checks = get_training_checks().get(username, {})
_grad_done   = sum(
    1 for c in _grad_cats for item in c["items"]
    if _grad_checks.get(f"{c['name']}::{item}", False)
)
_grad_remaining = _grad_total - _grad_done

if _grad_remaining == 0:
    st.success("卒業条件をすべてクリアしています！先輩スタッフに確認してもらいましょう。")
else:
    st.markdown(
        f"<div style='background:white;border-radius:12px;padding:14px 20px;"
        f"box-shadow:0 2px 8px rgba(0,0,0,0.07);margin-bottom:16px;'>"
        f"<div style='display:flex;justify-content:space-between;margin-bottom:8px;'>"
        f"<span style='font-weight:700;'>卒業まであと <span style='color:#e85d04;'>"
        f"{_grad_remaining}</span> 項目</span>"
        f"<span style='color:#999;font-size:0.85rem;'>{_grad_done}/{_grad_total}</span>"
        f"</div>"
        f"<div style='background:#f0f0f0;border-radius:99px;height:8px;'>"
        f"<div style='background:linear-gradient(90deg,#e85d04,#f48c06);"
        f"width:{int(_grad_done/_grad_total*100) if _grad_total else 0}%;"
        f"height:8px;border-radius:99px;'></div></div>"
        f"<div style='margin-top:10px;'>",
        unsafe_allow_html=True,
    )
    for c in _grad_cats:
        cat_done = sum(1 for item in c["items"]
                       if _grad_checks.get(f"{c['name']}::{item}", False))
        icon = "✅" if cat_done == len(c["items"]) else "○"
        st.markdown(
            f"<span style='font-size:0.82rem;margin-right:16px;color:"
            f"{'#28a745' if cat_done==len(c['items']) else '#555'};'>"
            f"{icon} {c['name']} {cat_done}/{len(c['items'])}</span>",
            unsafe_allow_html=True,
        )
    st.markdown("</div></div>", unsafe_allow_html=True)

st.write("")

tab_fc, tab_quiz, tab_stamps = st.tabs(["フラッシュカード", "クイズ", "スタンプ帳"])

# ════ フラッシュカード ══════════════════════════════════════════
with tab_fc:
    order = st.session_state.fc_order
    idx   = st.session_state.fc_index
    card  = FLASHCARDS[order[idx]]

    st.progress((idx + 1) / len(order))
    st.caption(f"カード {idx + 1} / {len(order)}")

    if not st.session_state.fc_show_back:
        st.markdown(f"""
<div class="flashcard flashcard-front">
  <div class="fc-label">問題</div>
  <div class="fc-text">{card['front']}</div>
</div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""
<div class="flashcard flashcard-back">
  <div class="fc-label">答え</div>
  <div class="fc-text">{card['back']}</div>
</div>""", unsafe_allow_html=True)

    st.write("")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("前へ", use_container_width=True, disabled=(idx == 0)):
            st.session_state.fc_index -= 1
            st.session_state.fc_show_back = False
            st.rerun()
    with c2:
        label = "隠す" if st.session_state.fc_show_back else "答えを見る"
        if st.button(label, use_container_width=True, type="primary"):
            st.session_state.fc_show_back = not st.session_state.fc_show_back
            st.rerun()
    with c3:
        if st.button("次へ", use_container_width=True, disabled=(idx == len(order) - 1)):
            st.session_state.fc_index += 1
            st.session_state.fc_show_back = False
            st.rerun()
    with c4:
        if st.button("シャッフル", use_container_width=True):
            new_order = list(range(len(FLASHCARDS)))
            random.shuffle(new_order)
            st.session_state.fc_order = new_order
            st.session_state.fc_index = 0
            st.session_state.fc_show_back = False
            st.rerun()

    with st.expander("全カード一覧"):
        for i, card in enumerate(FLASHCARDS):
            st.markdown(f"**{i+1}. {card['front']}** — {card['back']}")

# ════ クイズ ════════════════════════════════════════════════════
with tab_quiz:
    if not st.session_state.quiz_started:
        st.markdown("""
<div class="info-card" style="text-align:center; padding: 30px;">
  <div style="font-size:3rem;">🎯</div>
  <div style="font-size:1.3rem; font-weight:700; margin:12px 0;">全10問チャレンジ！</div>
  <div style="color:#666;">接客・衛生・メニューなど幅広く出題。合格ラインは7問以上！</div>
</div>""", unsafe_allow_html=True)
        st.write("")
        if st.button("クイズをスタート", type="primary", use_container_width=True):
            order = list(range(len(QUIZ)))
            random.shuffle(order)
            st.session_state.quiz_order   = order
            st.session_state.quiz_index   = 0
            st.session_state.quiz_score   = 0
            st.session_state.quiz_answers = []
            st.session_state.quiz_started  = True
            st.session_state.quiz_finished = False
            st.rerun()

    elif st.session_state.quiz_finished:
        score = st.session_state.quiz_score
        total = len(QUIZ)
        pct   = score / total * 100

        if pct == 100:
            st.success(f"パーフェクト！ {score}/{total}問正解！完璧です！")
            st.balloons()
        elif pct >= 70:
            st.success(f"合格！ {score}/{total}問正解（{pct:.0f}%）よくできました！")
        else:
            st.warning(f"あと少し！ {score}/{total}問正解（{pct:.0f}%）もう一度チャレンジしよう！")

        # 進捗保存
        prog = get_progress(username)
        prog["quiz_scores"]   = prog.get("quiz_scores", []) + [score]
        prog["quiz_attempts"] = prog.get("quiz_attempts", 0) + 1
        save_progress(username, prog)
        _, new_stamps = award_stamps(username)
        show_new_stamps(new_stamps)

        st.write("### 解答結果")
        for i, (ans, q_idx) in enumerate(zip(st.session_state.quiz_answers, st.session_state.quiz_order)):
            q  = QUIZ[q_idx]
            ok = ans == q["answer"]
            with st.expander(f"{'✅' if ok else '❌'} Q{i+1}: {q['q']}"):
                for j, ch in enumerate(q["choices"]):
                    if j == q["answer"]:
                        st.success(f"✅ {ch}（正解）")
                    elif j == ans and not ok:
                        st.error(f"❌ {ch}（あなたの答え）")
                    else:
                        st.write(f"　{ch}")
                st.info(f"解説: {q['exp']}")

        st.write("")
        if st.button("もう一度挑戦する", type="primary", use_container_width=True):
            st.session_state.quiz_started  = False
            st.session_state.quiz_finished = False
            st.rerun()

    else:
        q_idx      = st.session_state.quiz_index
        q_data_idx = st.session_state.quiz_order[q_idx]
        q          = QUIZ[q_data_idx]
        answered   = len(st.session_state.quiz_answers) > q_idx

        st.progress(q_idx / len(QUIZ))
        st.caption(f"問題 {q_idx + 1} / {len(QUIZ)}")
        st.subheader(q["q"])
        st.write("")

        for i, ch in enumerate(q["choices"]):
            if answered:
                if i == q["answer"]:
                    st.success(f"✅ {ch}")
                elif i == st.session_state.quiz_answers[q_idx]:
                    st.error(f"❌ {ch}")
                else:
                    st.button(ch, key=f"q{q_idx}_{i}", disabled=True, use_container_width=True)
            else:
                if st.button(ch, key=f"q{q_idx}_{i}", use_container_width=True):
                    st.session_state.quiz_answers.append(i)
                    if i == q["answer"]:
                        st.session_state.quiz_score += 1
                    st.rerun()

        if answered:
            is_correct = st.session_state.quiz_answers[q_idx] == q["answer"]
            if is_correct:
                st.markdown('<div class="quiz-result-correct">✅ 正解！</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div class="quiz-result-wrong">❌ 不正解。正解は「{q["choices"][q["answer"]]}」</div>',
                    unsafe_allow_html=True,
                )
            st.info(f"解説: {q['exp']}")
            st.write("")
            btn_label = "次の問題へ" if q_idx + 1 < len(QUIZ) else "結果を見る"
            if st.button(btn_label, type="primary", use_container_width=True):
                if q_idx + 1 < len(QUIZ):
                    st.session_state.quiz_index += 1
                else:
                    st.session_state.quiz_finished = True
                st.rerun()

# ════ スタンプ帳 ═════════════════════════════════════════════
with tab_stamps:
    prog         = get_progress(username)
    earned       = set(prog.get("stamps", []))
    earned_count = len(earned)
    total_stamps = len(STAMPS)

    st.progress(earned_count / total_stamps)
    st.caption(f"獲得: {earned_count} / {total_stamps} スタンプ")
    st.write("")

    stamp_html = '<div class="stamp-grid">'
    for key, info in STAMPS.items():
        locked = key not in earned
        cls    = "locked" if locked else ""
        stamp_html += f"""
<div class="stamp-item">
  <div class="stamp-circle {cls}" title="{info['desc']}">{info['emoji']}</div>
  <div class="stamp-name {cls}">{info['name']}</div>
</div>"""
    stamp_html += "</div>"
    st.markdown(stamp_html, unsafe_allow_html=True)

    st.divider()
    st.markdown("#### スタンプ獲得条件")
    for key, info in STAMPS.items():
        earned_icon = "✅" if key in earned else "🔒"
        st.markdown(f"{earned_icon} **{info['emoji']} {info['name']}** — {info['desc']}")

    # クイズ成績グラフ
    scores = prog.get("quiz_scores", [])
    if scores:
        st.divider()
        st.markdown("#### クイズ成績の推移")
        import pandas as pd
        df = pd.DataFrame({"得点": scores, "回": range(1, len(scores)+1)})
        st.line_chart(df.set_index("回")["得点"])
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("最高点", f"{max(scores)}/10")
        with col2:
            st.metric("平均点", f"{sum(scores)/len(scores):.1f}/10")
        with col3:
            st.metric("挑戦回数", f"{len(scores)}回")
