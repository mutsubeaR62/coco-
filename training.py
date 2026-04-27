import streamlit as st
import random
import json
from datetime import datetime

st.set_page_config(page_title="CoCo壱番屋 新人トレーニング", page_icon="🍛", layout="wide")

# ─── スタイル ───────────────────────────────────────────────────
st.markdown("""
<style>
    .main-title {
        background: linear-gradient(90deg, #e85d04, #f48c06);
        color: white; padding: 20px; border-radius: 12px;
        text-align: center; font-size: 2rem; font-weight: bold;
        margin-bottom: 20px;
    }
    .card {
        background: #fff8f0; border: 2px solid #f48c06;
        border-radius: 12px; padding: 20px; margin: 10px 0;
    }
    .correct { background: #d4edda; border: 2px solid #28a745; border-radius: 8px; padding: 10px; }
    .wrong   { background: #f8d7da; border: 2px solid #dc3545; border-radius: 8px; padding: 10px; }
    .flashcard-front {
        background: linear-gradient(135deg, #e85d04, #f48c06);
        color: white; border-radius: 16px; padding: 40px;
        text-align: center; font-size: 1.8rem; font-weight: bold;
        min-height: 160px; display: flex; align-items: center; justify-content: center;
    }
    .flashcard-back {
        background: linear-gradient(135deg, #2d6a4f, #40916c);
        color: white; border-radius: 16px; padding: 40px;
        text-align: center; font-size: 1.4rem;
        min-height: 160px; display: flex; align-items: center; justify-content: center;
    }
    .stButton > button {
        border-radius: 8px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🍛 CoCo壱番屋 新人トレーニングアプリ</div>', unsafe_allow_html=True)

# ─── データ ────────────────────────────────────────────────────
QUIZ_DATA = [
    {
        "q": "CoCo壱番屋のカレーの辛さは何種類ありますか？",
        "choices": ["5種類", "8種類", "10種類", "12種類"],
        "answer": 2,
        "explanation": "辛さは0倍〜10辛まで11段階（＋辛さなし）。5辛以上は辛さへの覚悟が必要です！"
    },
    {
        "q": "ライスのサイズで「並」は何グラムですか？",
        "choices": ["200g", "250g", "300g", "350g"],
        "answer": 2,
        "explanation": "並は300g。他に200g(少なめ)・400g・500g・600g・700g・800g・900g・1000gが選べます。"
    },
    {
        "q": "お客様が辛さ変更を注文された場合、5辛以上のとき何を確認しますか？",
        "choices": ["年齢確認", "辛さへの同意確認", "アレルギー確認", "特に何もしない"],
        "answer": 1,
        "explanation": "5辛以上は辛さの確認をお客様にしっかり行います。体調不良防止のためです。"
    },
    {
        "q": "食器を洗う際の正しい順番はどれですか？",
        "choices": [
            "油もの→汚れ少ない食器→グラス",
            "グラス→汚れ少ない食器→油もの",
            "汚れ少ない食器→グラス→油もの",
            "順番はどれでも同じ"
        ],
        "answer": 1,
        "explanation": "汚れの少ないものから洗うのが基本。グラス→汚れ少ない食器→油ものの順で水がきれいに保てます。"
    },
    {
        "q": "接客の基本「いらっしゃいませ」はいつ言いますか？",
        "choices": ["お客様が席についたとき", "お客様が入口から入ったとき", "注文を受けるとき", "料理を提供するとき"],
        "answer": 1,
        "explanation": "入口から入った瞬間に元気よく「いらっしゃいませ」。第一印象が大切です！"
    },
    {
        "q": "アレルギーの申告をされたお客様への対応として正しいのはどれですか？",
        "choices": [
            "自分で判断して答える",
            "店長・社員に必ず確認を取る",
            "メニュー表だけ渡す",
            "対応できないと断る"
        ],
        "answer": 1,
        "explanation": "アレルギー対応は命にかかわります。必ず店長・社員に確認を取り、責任ある対応をしてください。"
    },
    {
        "q": "カレーのルーが余った場合の正しい処理は？",
        "choices": ["次の日まで保存して使う", "所定の廃棄処理をする", "スタッフが持ち帰る", "そのまま鍋に残しておく"],
        "answer": 1,
        "explanation": "衛生管理上、余ったルーは規定に従い廃棄処理します。食品ロスを減らすためにも適切な量の管理が大切です。"
    },
    {
        "q": "お客様から「ごちそうさまでした」と言われたとき、何と返しますか？",
        "choices": ["「はい」", "「ありがとうございます」", "「ありがとうございました。またお越しくださいませ」", "「お気をつけて」"],
        "answer": 2,
        "explanation": "「ありがとうございました。またお越しくださいませ」が基本の接客用語です。感謝の気持ちを込めて！"
    },
    {
        "q": "トッピングの「福神漬け」は何色ですか？",
        "choices": ["黄色", "赤色（ピンク）", "緑色", "白色"],
        "answer": 1,
        "explanation": "CoCo壱番屋の福神漬けは赤色（ピンク）。カレーの色との組み合わせが特徴的です。"
    },
    {
        "q": "手洗いはいつ行うべきですか？（複数の状況から最も重要なもの）",
        "choices": [
            "トイレの後だけ",
            "出勤時だけ",
            "トイレの後・生食材を触った後・ゴミ処理後など、こまめに",
            "1時間に1回"
        ],
        "answer": 2,
        "explanation": "食品衛生の基本。トイレ後、生食材後、ゴミ処理後など、あらゆる場面でこまめに手洗いしましょう。"
    },
]

FLASHCARD_DATA = [
    {"front": "辛さ 1辛", "back": "ほんのり辛い。辛いものが苦手な方にもおすすめ"},
    {"front": "辛さ 3辛", "back": "標準的な辛さ。辛さが好きな人に人気"},
    {"front": "辛さ 5辛", "back": "しっかり辛い。5辛以上は辛さ確認が必要"},
    {"front": "辛さ 10辛", "back": "最高辛さ。唐辛子ベースの激辛。注文時に要確認"},
    {"front": "ライス 並", "back": "300g（基本のサイズ）"},
    {"front": "ライス 大", "back": "400g"},
    {"front": "ライス 特大", "back": "500g"},
    {"front": "ライス 少なめ", "back": "200g（並より少ない）"},
    {"front": "福神漬け", "back": "カレーに添えられる赤い漬物。無料トッピング"},
    {"front": "らっきょう", "back": "カレーに合う甘酸っぱい漬物。有料トッピング"},
    {"front": "ロースカツ", "back": "豚ロース肉のカツ。CoCo壱番屋の定番トッピング"},
    {"front": "チキンカツ", "back": "鶏むね肉のカツ。ロースカツよりあっさり"},
    {"front": "いらっしゃいませ", "back": "お客様が入店したときに言う最初の挨拶"},
    {"front": "ありがとうございました", "back": "お客様が退店するときの感謝の言葉"},
    {"front": "少々お待ちくださいませ", "back": "お客様に待っていただくときの言葉"},
    {"front": "HACCP", "back": "食品衛生管理の国際基準。危害要因を分析・管理する仕組み"},
    {"front": "クロスコンタミネーション", "back": "食材の交差汚染。アレルゲンが別の食材につくこと。防止が重要"},
    {"front": "QSC", "back": "Quality（品質）・Service（サービス）・Cleanliness（清潔）飲食業の基本3原則"},
]

CHECKLIST_DATA = {
    "開店前チェック": [
        "ユニフォームを正しく着用している（名札含む）",
        "手洗い・うがいを済ませた",
        "体調に問題がない（発熱・下痢・嘔吐がない）",
        "ホールの清掃（床・テーブル・椅子）を完了した",
        "メニュー表・卓上の備品が揃っている",
        "調味料類（ソース・塩・胡椒など）の補充を確認した",
        "トイレ清掃を行った",
        "POSレジの起動確認をした",
        "食材の在庫確認をした",
        "ゴミ箱のゴミを捨て、新しいゴミ袋をセットした",
    ],
    "接客中チェック": [
        "お客様が入店したら即座に「いらっしゃいませ」と声かけ",
        "テーブルへの案内・メニューの提供",
        "注文内容を正確に復唱確認した",
        "辛さ5辛以上の場合、辛さ確認を行った",
        "アレルギー申告があった場合、店長・社員に報告した",
        "料理提供時に品名を言った",
        "空いた食器はこまめに下げた",
        "テーブルは常に清潔に保った",
        "お会計は正確に行った",
        "退店時に「ありがとうございました。またお越しくださいませ」",
    ],
    "閉店作業チェック": [
        "食材の適切な保管・廃棄処理を行った",
        "全テーブル・椅子を清拭した",
        "床の清掃（掃き掃除・モップがけ）を完了した",
        "トイレの最終清掃を行った",
        "厨房の清掃（コンロ・フライヤー周辺）を完了した",
        "食器・調理器具を洗浄・消毒した",
        "翌日の食材準備・発注確認をした",
        "レジの締め作業を行った",
        "ゴミの分別・搬出を行った",
        "施錠・消灯確認をした",
    ],
    "衛生管理チェック": [
        "出勤時に手洗い・うがいをした",
        "調理前に手洗いをした",
        "トイレ後に手洗いをした",
        "生の食材を触った後に手洗いをした",
        "ゴミ処理後に手洗いをした",
        "手指の傷がある場合、手袋を使用している",
        "爪は短く切り揃えている",
        "髪の毛をまとめ、帽子を着用している",
        "アクセサリーを外している",
        "食品の温度管理を適切に行っている",
    ],
}

MANUAL_DATA = {
    "接客の基本": {
        "icon": "👋",
        "content": """
### 接客7大用語
| 場面 | 言葉 |
|------|------|
| 入店時 | いらっしゃいませ |
| 案内時 | こちらへどうぞ |
| 注文受付 | ご注文はお決まりですか？ |
| 待たせるとき | 少々お待ちくださいませ |
| 料理提供 | お待たせいたしました。〇〇でございます |
| お礼 | ありがとうございます |
| 退店時 | ありがとうございました。またお越しくださいませ |

### 笑顔と声量
- 笑顔は接客の基本。お客様は鏡のようにスタッフの表情を映します
- 声は少し大きめ、明るいトーンで
- お客様の目を見て話す

### NGな接客
- 「はい」のみの返答（「はい、かしこまりました」が正解）
- 友達言葉（「了解です」「そうですね」など）
- 背を向けたまま話す
        """
    },
    "辛さ・ライスのルール": {
        "icon": "🌶️",
        "content": """
### 辛さレベル一覧
| レベル | 特徴 |
|--------|------|
| 辛さなし | 辛さゼロ。お子様・辛いもの苦手な方に |
| 1辛 | ほんのり辛い |
| 2辛 | 少し辛い |
| 3辛 | 標準的な辛さ |
| 4辛 | かなり辛い |
| 5辛〜 | ⚠️ 辛さ確認が必要 |
| 10辛 | 最高辛さ。激辛 |

### 5辛以上の対応
1. 注文を受けたら「5辛以上はかなり辛いですが大丈夫ですか？」と確認
2. お客様の同意を得てから通す
3. 無理に止めず、確認したうえで尊重する

### ライスサイズ
200g（少）→ 300g（並）→ 400g（大）→ 500g（特大）→ 600〜1000g
        """
    },
    "衛生管理": {
        "icon": "🧼",
        "content": """
### 手洗いのタイミング（必須）
- 出勤時
- 調理・食材を触る前
- トイレ使用後
- 生の食材（肉・魚）を触った後
- ゴミ処理後
- 咳・くしゃみ・鼻をかんだ後
- 休憩後

### 正しい手洗いの手順
1. 流水で手を濡らす
2. 石けんを十分に泡立てる
3. 手のひら・手の甲・指の間・爪の中を20秒以上洗う
4. 流水でしっかり流す
5. ペーパータオルで拭く（ハンカチ不可）

### 食品温度管理
- 冷蔵品: **10℃以下**
- 冷凍品: **-18℃以下**
- 加熱調理: **75℃以上・1分以上**

### アレルギー対応
⚠️ アレルギーの申告があったら**必ず店長・社員に報告**
自己判断での対応は絶対にしない
        """
    },
    "トラブル対応": {
        "icon": "🚨",
        "content": """
### クレーム対応の基本手順
1. **まず謝罪・傾聴** — 「申し訳ございません」と誠意を示す
2. **事実確認** — 何が起きたかを落ち着いて聞く
3. **上司報告** — 必ず店長・社員に報告する
4. **解決策の提示** — 上司の指示に従い対応する
5. **再発防止** — チームで共有・改善する

### NGな対応
- その場で言い訳する
- 感情的になる
- 自分だけで解決しようとする
- お客様を長時間お待たせする

### よくあるトラブル
| 状況 | 初期対応 |
|------|--------|
| 注文間違い | すぐ謝罪・店長報告・作り直し |
| 異物混入 | お客様から回収・謝罪・店長報告 |
| お客様の気分不良 | 静かな場所に案内・水を提供・救急対応確認 |
| レジミス | 店長に確認・正確に対応 |

### 緊急連絡先
- **店長に真っ先に報告する**
- 火災・地震など: 消防署 **119** / 警察 **110**
        """
    },
    "開店・閉店作業": {
        "icon": "🔑",
        "content": """
### 開店前の流れ
1. 出勤・ロッカーでユニフォームに着替え
2. 体調チェック（発熱・下痢・嘔吐がないか）
3. 手洗い
4. 朝礼・本日の確認事項共有
5. ホール清掃（テーブル・椅子・床）
6. 備品チェック・補充
7. 食材確認
8. レジ起動・釣り銭確認
9. 開店！

### 閉店作業の流れ
1. ラストオーダーの対応
2. 食材の保管・廃棄処理
3. ホール清掃
4. 厨房清掃
5. 食器・調理器具の洗浄・消毒
6. レジ締め
7. ゴミ分別・搬出
8. 消灯・施錠確認
9. 退勤報告

### ポイント
- 一人でやらず、チームで分担して効率よく
- わからないことは必ず確認してから行動
        """
    },
}

# ─── セッション初期化 ──────────────────────────────────────────
def init_session():
    defaults = {
        "quiz_index": 0,
        "quiz_score": 0,
        "quiz_answers": [],
        "quiz_started": False,
        "quiz_finished": False,
        "quiz_order": list(range(len(QUIZ_DATA))),
        "fc_index": 0,
        "fc_show_back": False,
        "fc_order": list(range(len(FLASHCARD_DATA))),
        "checklist_state": {cat: [False]*len(items) for cat, items in CHECKLIST_DATA.items()},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ─── タブ ──────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["📋 マニュアル", "🃏 フラッシュカード", "❓ クイズ", "✅ チェックリスト"])

# ════════════════════════════════════════════════════════════════
# TAB 1: マニュアル
# ════════════════════════════════════════════════════════════════
with tab1:
    st.header("📋 業務マニュアル")
    st.caption("基本的な業務内容を確認しよう！")

    for title, data in MANUAL_DATA.items():
        with st.expander(f"{data['icon']} {title}", expanded=False):
            st.markdown(data["content"])

# ════════════════════════════════════════════════════════════════
# TAB 2: フラッシュカード
# ════════════════════════════════════════════════════════════════
with tab2:
    st.header("🃏 フラッシュカード")
    st.caption("カードをめくって覚えよう！")

    col_nav, col_info = st.columns([3, 1])
    with col_info:
        fc_idx = st.session_state.fc_index
        fc_order = st.session_state.fc_order
        st.metric("進捗", f"{fc_idx + 1} / {len(fc_order)}")

    current_card = FLASHCARD_DATA[fc_order[fc_idx]]

    if not st.session_state.fc_show_back:
        st.markdown(f'<div class="flashcard-front">❓ {current_card["front"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="flashcard-back">💡 {current_card["back"]}</div>', unsafe_allow_html=True)

    st.write("")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("⬅️ 前へ", use_container_width=True):
            st.session_state.fc_index = max(0, fc_idx - 1)
            st.session_state.fc_show_back = False
            st.rerun()
    with col2:
        label = "🔄 答えを隠す" if st.session_state.fc_show_back else "💡 答えを見る"
        if st.button(label, use_container_width=True):
            st.session_state.fc_show_back = not st.session_state.fc_show_back
            st.rerun()
    with col3:
        if st.button("➡️ 次へ", use_container_width=True):
            st.session_state.fc_index = min(len(fc_order) - 1, fc_idx + 1)
            st.session_state.fc_show_back = False
            st.rerun()
    with col4:
        if st.button("🔀 シャッフル", use_container_width=True):
            new_order = list(range(len(FLASHCARD_DATA)))
            random.shuffle(new_order)
            st.session_state.fc_order = new_order
            st.session_state.fc_index = 0
            st.session_state.fc_show_back = False
            st.rerun()

    st.write("")
    progress_val = (fc_idx + 1) / len(fc_order)
    st.progress(progress_val)

    # カード一覧
    with st.expander("📄 全カード一覧"):
        for i, card in enumerate(FLASHCARD_DATA):
            st.markdown(f"**{i+1}. {card['front']}** — {card['back']}")

# ════════════════════════════════════════════════════════════════
# TAB 3: クイズ
# ════════════════════════════════════════════════════════════════
with tab3:
    st.header("❓ 確認クイズ")
    st.caption("業務知識をテストしよう！全問正解を目指せ！")

    if not st.session_state.quiz_started:
        st.markdown('<div class="card">📝 全10問のクイズに挑戦しよう！<br>接客・衛生・メニューなど幅広く出題されます。</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("🎯 クイズをスタート！", use_container_width=True, type="primary"):
                order = list(range(len(QUIZ_DATA)))
                random.shuffle(order)
                st.session_state.quiz_order = order
                st.session_state.quiz_index = 0
                st.session_state.quiz_score = 0
                st.session_state.quiz_answers = []
                st.session_state.quiz_started = True
                st.session_state.quiz_finished = False
                st.rerun()

    elif st.session_state.quiz_finished:
        score = st.session_state.quiz_score
        total = len(QUIZ_DATA)
        pct = score / total * 100

        if pct == 100:
            st.success(f"🎉 パーフェクト！ {score}/{total}問正解！")
            st.balloons()
        elif pct >= 70:
            st.info(f"👍 合格ライン！ {score}/{total}問正解（{pct:.0f}%）")
        else:
            st.warning(f"📚 もう少し！ {score}/{total}問正解（{pct:.0f}%）。もう一度復習しよう！")

        st.write("### 解答結果")
        for i, (ans, q_idx) in enumerate(zip(st.session_state.quiz_answers, st.session_state.quiz_order)):
            q = QUIZ_DATA[q_idx]
            is_correct = ans == q["answer"]
            icon = "✅" if is_correct else "❌"
            with st.expander(f"{icon} Q{i+1}: {q['q']}"):
                st.write(f"あなたの答え: **{q['choices'][ans]}**")
                if not is_correct:
                    st.write(f"正解: **{q['choices'][q['answer']]}**")
                st.info(f"💡 {q['explanation']}")

        if st.button("🔄 もう一度挑戦", type="primary"):
            st.session_state.quiz_started = False
            st.session_state.quiz_finished = False
            st.rerun()

    else:
        q_idx = st.session_state.quiz_index
        total = len(QUIZ_DATA)
        q_data_idx = st.session_state.quiz_order[q_idx]
        q = QUIZ_DATA[q_data_idx]

        st.progress((q_idx) / total)
        st.caption(f"問題 {q_idx + 1} / {total}")
        st.subheader(q["q"])

        already_answered = len(st.session_state.quiz_answers) > q_idx

        for i, choice in enumerate(q["choices"]):
            btn_key = f"choice_{q_idx}_{i}"
            if already_answered:
                is_correct = i == q["answer"]
                is_selected = i == st.session_state.quiz_answers[q_idx]
                if is_correct:
                    st.success(f"✅ {choice}")
                elif is_selected:
                    st.error(f"❌ {choice}")
                else:
                    st.button(choice, key=btn_key, disabled=True, use_container_width=True)
            else:
                if st.button(choice, key=btn_key, use_container_width=True):
                    st.session_state.quiz_answers.append(i)
                    if i == q["answer"]:
                        st.session_state.quiz_score += 1
                    st.rerun()

        if already_answered:
            selected = st.session_state.quiz_answers[q_idx]
            if selected == q["answer"]:
                st.markdown('<div class="correct">✅ 正解！</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="wrong">❌ 不正解。正解は「{q["choices"][q["answer"]]}」</div>', unsafe_allow_html=True)
            st.info(f"💡 {q['explanation']}")

            st.write("")
            if q_idx + 1 < total:
                if st.button("次の問題へ ➡️", type="primary"):
                    st.session_state.quiz_index += 1
                    st.rerun()
            else:
                if st.button("結果を見る 🏁", type="primary"):
                    st.session_state.quiz_finished = True
                    st.rerun()

# ════════════════════════════════════════════════════════════════
# TAB 4: チェックリスト
# ════════════════════════════════════════════════════════════════
with tab4:
    st.header("✅ 業務チェックリスト")
    st.caption("作業ごとに確認しながらチェックしよう！")

    # リセットボタン
    col_r, col_s = st.columns([3, 1])
    with col_s:
        if st.button("🔄 全リセット"):
            st.session_state.checklist_state = {
                cat: [False]*len(items) for cat, items in CHECKLIST_DATA.items()
            }
            st.rerun()

    total_items = sum(len(v) for v in CHECKLIST_DATA.values())
    checked_items = sum(
        sum(1 for c in checks if c)
        for checks in st.session_state.checklist_state.values()
    )
    st.progress(checked_items / total_items)
    st.caption(f"完了: {checked_items} / {total_items} 項目")

    for cat, items in CHECKLIST_DATA.items():
        checks = st.session_state.checklist_state[cat]
        done = sum(checks)
        with st.expander(f"{'✅' if done == len(items) else '📋'} {cat} ({done}/{len(items)})", expanded=True):
            for i, item in enumerate(items):
                new_val = st.checkbox(item, value=checks[i], key=f"cl_{cat}_{i}")
                if new_val != checks[i]:
                    st.session_state.checklist_state[cat][i] = new_val
                    st.rerun()

    if checked_items == total_items:
        st.success("🎉 全項目完了！お疲れ様でした！")
        st.balloons()
