import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from datetime import datetime
from utils import (apply_theme, require_login, page_header, load_json, save_json,
                   get_progress, save_progress, award_stamps, show_new_stamps,
                   is_manager, render_attachments, upload_attachment_ui)

apply_theme()
require_login()

user = st.session_state.user
username = user["username"]

# ─── チェックリストデータ（動機付けコメント付き） ──────────────
DEFAULT_CHECKLISTS = {
    "checklists": [
        {
            "id": "opening",
            "name": "開店前チェック",
            "icon": "🌅",
            "items": [
                {"task": "ユニフォームを正しく着用する（名札含む）",
                 "why": "清潔な身だしなみは第一印象を決める。社会人として「外見から誠実さを伝える」スキルは一生使えます。"},
                {"task": "手洗い・うがいを済ませる",
                 "why": "衛生意識の習慣化。どの職場でも「清潔感のある人」として評価されます。"},
                {"task": "体調に問題がないか確認する（発熱・下痢・嘔吐がない）",
                 "why": "自己管理力はプロ意識の証。自分の体調をきちんと把握し報告できる人が職場で信頼されます。"},
                {"task": "ホールの清掃（床・テーブル・椅子）を完了する",
                 "why": "環境整備力。整った環境を維持する習慣は、どの職場でも求められる基礎スキルです。"},
                {"task": "メニュー表・卓上備品が揃っているか確認し補充する",
                 "why": "先読みして準備する力（段取り力）。仕事の効率化の基本で、社会人としての評価に直結します。"},
                {"task": "調味料類の補充を確認する",
                 "why": "「なくなる前に補充」という先読み習慣は在庫管理の基礎。管理能力として高く評価されます。"},
                {"task": "トイレ清掃を行う",
                 "why": "「トイレ掃除が丁寧な人は仕事も丁寧」と言われます。目に見えない場所への気配りが信頼を生みます。"},
                {"task": "POSレジの起動・釣り銭確認をする",
                 "why": "数字への責任感と確認作業の徹底。金銭を正確に扱う能力はどんな仕事でも信頼の証です。"},
                {"task": "食材の在庫確認をする",
                 "why": "ロス削減・コスト意識の基礎。「会社のお金を大切にする感覚」が身につきます。"},
                {"task": "ゴミ箱を空にし新しいゴミ袋をセットする",
                 "why": "次の人のための準備。「自分の後のことを考える行動」がチームワークの基本です。"},
            ]
        },
        {
            "id": "service",
            "name": "接客中チェック",
            "icon": "👋",
            "items": [
                {"task": "入店したお客様に即座に「いらっしゃいませ」と声をかける",
                 "why": "反応速度と気配りの訓練。「気づいてもらえた」という感覚は人間関係全般で重要なスキルです。"},
                {"task": "テーブルへ丁寧に案内し、メニューを提供する",
                 "why": "相手の立場で考える力。「相手の次のステップを予測して行動する」姿勢はビジネス全般で評価されます。"},
                {"task": "注文内容を正確に復唱・確認する",
                 "why": "報告・連絡・確認（ホウレンソウ）の実践。ミスを防ぐ確認習慣はどんな職場でも最重要スキルです。"},
                {"task": "5辛以上の場合、辛さ確認を行う",
                 "why": "お客様の安全を守る責任感と「リスク管理」の実践。相手への配慮を行動で示せる人になれます。"},
                {"task": "アレルギー申告があった場合、店長・社員に必ず報告する",
                 "why": "判断を適切に委ねる力。「自分で抱えず、適切な人に繋げる」判断力は社会人に非常に重要です。"},
                {"task": "料理を提供するときに品名を告げる",
                 "why": "明確なコミュニケーションの実践。「伝わることを確認する」習慣は説明力・報告力に直結します。"},
                {"task": "空いた食器をこまめに下げる",
                 "why": "周囲の状況を常に観察する力（観察力）。環境の変化に気づいて動ける人はどこでも重宝されます。"},
                {"task": "テーブルを常に清潔に保つ",
                 "why": "品質基準を継続して維持するプロ意識。一時的ではなく「常に高い水準を保つ姿勢」が評価されます。"},
                {"task": "お会計を正確に行う",
                 "why": "数字への正確さと誠実さ。お金を扱う緊張感と責任感は、社会人の基礎力として直結します。"},
                {"task": "退店時に「ありがとうございました。またお越しくださいませ」と声かけする",
                 "why": "最後まで丁寧に対応する「締めくくり力」。最後の印象が次の来店につながる、ビジネスの基本です。"},
            ]
        },
        {
            "id": "closing",
            "name": "閉店作業チェック",
            "icon": "🌙",
            "items": [
                {"task": "食材を適切に保管・廃棄処理する",
                 "why": "コスト意識と衛生管理の両立。「利益」と「安全」を同時に考える経営感覚が身につきます。"},
                {"task": "全テーブル・椅子を清拭する",
                 "why": "「次に使う人のため」に動く先見性。これがチームで動く上での基本的な思いやりです。"},
                {"task": "床の清掃（掃き掃除・モップがけ）を行う",
                 "why": "「やり切る力」。7割でなく100%仕上げる習慣が、一流の仕事人としての評価につながります。"},
                {"task": "トイレの最終清掃を行う",
                 "why": "誰も見ていない場所でも丁寧にやれる誠実さ。この姿勢は必ず人から信頼されます。"},
                {"task": "厨房の清掃（コンロ・フライヤー周辺）を行う",
                 "why": "プロとしての設備ケア意識。機器を大切に扱うことはコスト削減にも直結します。"},
                {"task": "食器・調理器具を洗浄・消毒する",
                 "why": "見えない菌への意識と科学的思考。安全管理の基礎を実践から学べます。"},
                {"task": "翌日の食材準備・発注確認をする",
                 "why": "前日準備の習慣。「明日の自分・チームのために今何をするか」を考える先読み力が育ちます。"},
                {"task": "レジの締め作業を行う",
                 "why": "一日の業務を数字で締めくくる習慣。売上管理・数値への責任感は社会人に必須のスキルです。"},
                {"task": "ゴミの分別・搬出を行う",
                 "why": "環境への配慮と地域ルールの遵守。社会的責任感（CSR意識）の基礎が身につきます。"},
                {"task": "消灯・施錠を確認する",
                 "why": "「最後に確認する」習慣。締めくくりを確実にする責任感は、どの職場でも信頼の源になります。"},
            ]
        },
        {
            "id": "hygiene",
            "name": "衛生管理チェック",
            "icon": "🧼",
            "items": [
                {"task": "出勤時に手洗い・うがいをした",
                 "why": "食品衛生の第一歩。自分とお客様の安全を守る意識がプロとしての責任感を育てます。"},
                {"task": "調理前に手洗いをした",
                 "why": "「触れるものに責任を持つ」意識の醸成。この繊細な衛生感覚は、どの職場でも信頼されます。"},
                {"task": "トイレ後に手洗いをした",
                 "why": "基本的な衛生習慣の徹底。当たり前のことを当たり前にできる人が、社会で最も信頼されます。"},
                {"task": "生の食材（肉・魚）を触った後に手洗いをした",
                 "why": "交差汚染（クロスコンタミネーション）防止。食の安全に対する科学的な理解が深まります。"},
                {"task": "ゴミ処理後に手洗いをした",
                 "why": "見えないリスクを想定して行動できる先読み力。安全管理の基本姿勢です。"},
                {"task": "手指に傷がある場合、手袋を着用した",
                 "why": "自己申告と適切な処置。自分の状態を正直に報告できる誠実さが信頼を生みます。"},
                {"task": "爪を短く切り揃えている",
                 "why": "細部への気配り。「小さいことに丁寧に向き合える人」は大きな仕事も丁寧にこなせます。"},
                {"task": "髪をまとめ、帽子を着用している",
                 "why": "規則への遵守とプロとしての身だしなみ。ルールを守る習慣は社会人としての信頼の基盤です。"},
                {"task": "アクセサリーを外している",
                 "why": "安全と品質への配慮。TPOを理解して装飾より機能を優先できる「判断力」が育ちます。"},
                {"task": "食品の温度管理を適切に行っている",
                 "why": "科学的な安全管理の実践。数値基準を守る几帳面さはどの業界でも品質管理の基礎スキルです。"},
            ]
        },
    ]
}

def get_checklists():
    data = load_json("checklists.json")
    if not data.get("checklists"):
        save_json("checklists.json", DEFAULT_CHECKLISTS)
        return DEFAULT_CHECKLISTS["checklists"]
    return data["checklists"]

# ─── セッション初期化 ─────────────────────────────────────────
def init_cl_session(checklists):
    if "cl_state" not in st.session_state:
        st.session_state.cl_state = {
            cl["name"]: [False] * len(cl["items"])
            for cl in checklists
        }
    if "cl_show_why" not in st.session_state:
        st.session_state.cl_show_why = {}

# ─── ページ ──────────────────────────────────────────────────
page_header("✅ チェックリスト", "作業ごとに確認しながら進めよう")

checklists = get_checklists()
init_cl_session(checklists)

role = user.get("role", "new")

# リセット + 全体進捗
col_info, col_reset = st.columns([4, 1])
total_items = sum(len(cl["items"]) for cl in checklists)
total_done = sum(
    sum(1 for c in st.session_state.cl_state.get(cl["name"], []) if c)
    for cl in checklists
)
with col_info:
    st.progress(total_done / max(total_items, 1))
    st.caption(f"全体進捗: {total_done} / {total_items} 項目完了")
with col_reset:
    if st.button("🔄 全リセット"):
        st.session_state.cl_state = {
            cl["name"]: [False] * len(cl["items"])
            for cl in checklists
        }
        st.rerun()

st.write("")

# ─── 各チェックリスト ─────────────────────────────────────────
for cl in checklists:
    cl_name = cl["name"]
    items = cl["items"]
    checks = st.session_state.cl_state.get(cl_name, [False] * len(items))
    done = sum(checks)
    all_done = done == len(items)

    icon = cl.get("icon", "📋")
    header = f"{'✅' if all_done else icon} {cl_name} ({done}/{len(items)})"

    with st.expander(header, expanded=not all_done):
        if all_done:
            st.success("🎉 このチェックリストをすべて完了しました！")

        # 添付ファイル表示
        render_attachments("checklist", cl["id"])

        show_why = st.toggle("💡 「なぜやるか」を表示", key=f"why_{cl_name}", value=False)

        for i, item in enumerate(items):
            col_check, col_label = st.columns([1, 12])
            with col_check:
                new_val = st.checkbox("", value=checks[i], key=f"cl_{cl_name}_{i}", label_visibility="collapsed")
            with col_label:
                style = "text-decoration: line-through; color: #999;" if checks[i] else ""
                st.markdown(f"<div style='{style} padding-top:4px;'>{item['task']}</div>", unsafe_allow_html=True)

            if new_val != checks[i]:
                st.session_state.cl_state[cl_name][i] = new_val
                st.rerun()

            if show_why:
                st.markdown(f'<div class="why-box">🔑 {item["why"]}</div>', unsafe_allow_html=True)

        # チェックリスト完了時に進捗保存
        new_done = sum(st.session_state.cl_state.get(cl_name, []))
        if new_done == len(items) and not all_done:
            prog = get_progress(username)
            cl_hist = prog.get("checklist_completions", {})
            cl_hist[cl_name] = cl_hist.get(cl_name, 0) + 1
            prog["checklist_completions"] = cl_hist
            save_progress(username, prog)
            _, new_stamps = award_stamps(username)
            show_new_stamps(new_stamps)

    # 完了時に記録ボタン
    new_checks = st.session_state.cl_state.get(cl_name, [])
    if sum(new_checks) == len(items):
        if st.button(f"📝 「{cl_name}」の完了を記録する", key=f"record_{cl_name}", type="primary"):
            prog = get_progress(username)
            cl_hist = prog.get("checklist_completions", {})
            cl_hist[cl_name] = cl_hist.get(cl_name, 0) + 1
            prog["checklist_completions"] = cl_hist
            save_progress(username, prog)
            _, new_stamps = award_stamps(username)
            show_new_stamps(new_stamps)
            # リセット
            st.session_state.cl_state[cl_name] = [False] * len(items)
            st.success(f"✅ 記録しました！（累計{cl_hist[cl_name]}回目）")
            st.rerun()

# 管理者・代行: ファイルアップロード
if is_manager(user):
    st.divider()
    with st.expander("📎 チェックリストへのファイル添付（管理者・代行）"):
        cl_data = load_json("checklists.json", DEFAULT_CHECKLISTS)
        for cl_item in cl_data.get("checklists", []):
            st.markdown(f"**{cl_item['icon']} {cl_item['name']}**")
            render_attachments("checklist", cl_item["id"], allow_delete=True)
            upload_attachment_ui("checklist", cl_item["id"], "写真・動画・ファイルをアップロード")
            st.divider()

# 管理者: チェックリスト編集
if role in ("admin", "daiko"):
    st.divider()
    with st.expander("⚙️ チェックリスト編集（管理者）"):
        data = load_json("checklists.json", DEFAULT_CHECKLISTS)
        all_cls = data.get("checklists", [])
        for ci, cl in enumerate(all_cls):
            st.markdown(f"##### {cl['icon']} {cl['name']}")
            for ii, item in enumerate(cl["items"]):
                col1, col2, col3 = st.columns([5, 5, 1])
                with col1:
                    new_task = st.text_input("タスク", value=item["task"], key=f"etask_{ci}_{ii}", label_visibility="collapsed")
                with col2:
                    new_why = st.text_input("なぜやるか", value=item.get("why", ""), key=f"ewhy_{ci}_{ii}", label_visibility="collapsed")
                with col3:
                    if st.button("🗑️", key=f"edel_{ci}_{ii}"):
                        all_cls[ci]["items"].pop(ii)
                        save_json("checklists.json", {"checklists": all_cls})
                        st.rerun()
                if new_task != item["task"] or new_why != item.get("why", ""):
                    all_cls[ci]["items"][ii] = {"task": new_task, "why": new_why}

            if st.button(f"➕ 「{cl['name']}」に項目追加", key=f"eadd_{ci}"):
                all_cls[ci]["items"].append({"task": "新しい項目", "why": "なぜやるかを入力"})
                save_json("checklists.json", {"checklists": all_cls})
                st.rerun()

        if st.button("💾 変更を保存", type="primary"):
            save_json("checklists.json", {"checklists": all_cls})
            st.success("保存しました！")
            st.rerun()
