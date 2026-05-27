import sys, os, re, base64
import fitz  # pymupdf
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_login, page_header, load_json, save_json,
                   get_progress, save_progress, award_stamps, show_new_stamps,
                   is_manager, render_attachments, upload_attachment_ui)

apply_theme()
require_login()

user = st.session_state.user
role = user.get("role", "new")

# ─── PDF フォルダ定義（フォルダ名 → 表示名） ──────────────────
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MANUAL_FOLDERS = [
    ("coco壱　カレーマニュアル", "🍛 カレーメニュー"),
    ("coco壱　マニュアル2",     "🥗 サイドメニュー等"),
]

# 後方互換のため既存変数も残す
PDF_DIR = os.path.join(BASE_DIR, "coco壱　カレーマニュアル")

# ─── デフォルト業務マニュアル ──────────────────────────────────
DEFAULT_MANUAL = {
    "sections": [
        {
            "id": "service_basics",
            "title": "接客の基本",
            "icon": "👋",
            "content": """
### 接客7大用語
| 場面 | 使う言葉 |
|------|--------|
| 入店時 | いらっしゃいませ |
| 案内時 | こちらへどうぞ |
| 注文時 | ご注文はお決まりですか？ |
| 待たせるとき | 少々お待ちくださいませ |
| 料理提供時 | お待たせいたしました。〇〇でございます |
| お礼 | ありがとうございます |
| 退店時 | ありがとうございました。またお越しくださいませ |

### NG接客
- 「了解です」「はい」だけで返す（→「かしこまりました」「はい、ただいま」）
- 背中を向けて話す
- お客様の前でスタッフ同士でおしゃべりする
- 無表情で対応する

### ポイント
- 笑顔は接客の基本！お客様はスタッフの表情に敏感です
- 声のトーンは明るめに。少し大きめがちょうどいい
- 「ついで確認」——他に何かご要望はありますか？を心がけよう
"""
        },
        {
            "id": "spice_rice",
            "title": "辛さ・ライスのルール",
            "icon": "🌶️",
            "content": """
### 辛さレベル
| レベル | 特徴 |
|--------|------|
| 辛さなし | 辛さゼロ。お子様・辛いものが苦手な方に |
| 1辛 | ほんのり辛い |
| 2辛 | 少し辛い |
| 3辛 | 標準的な辛さ（人気） |
| 4辛 | かなり辛い |
| **5辛以上** | ⚠️ **必ず辛さ確認が必要** |
| 10辛 | 最高辛さ・激辛 |

### 5辛以上の対応手順
1. 「5辛以上はかなり辛いですがよろしいですか？」と確認
2. お客様の同意を得てから通す
3. 強く止めず、確認したうえで意思を尊重する

### ライスサイズ
| サイズ | グラム |
|--------|--------|
| 少なめ | 200g |
| 並（基本） | 300g |
| 大 | 400g |
| 特大 | 500g |
| 600g〜1000g | 100g単位で注文可 |
"""
        },
        {
            "id": "hygiene",
            "title": "衛生管理",
            "icon": "🧼",
            "content": """
### 手洗いのタイミング（必須）
- 出勤時・調理前
- トイレ使用後
- 生の食材（肉・魚）を触った後
- ゴミ処理後
- 休憩後・咳・くしゃみ・鼻をかんだ後

### 正しい手洗い（20秒以上）
1. 流水で手を濡らす
2. 石けんをよく泡立てる
3. 手のひら・手の甲・指の間・爪の中を洗う
4. 流水で丁寧に流す
5. **ペーパータオル**で拭く（ハンカチ不可）

### 食品温度管理
| 種類 | 管理温度 |
|------|--------|
| 冷蔵品 | **10℃以下** |
| 冷凍品 | **-18℃以下** |
| 加熱調理 | **75℃以上・1分以上** |

### アレルギー対応
⚠️ アレルギー申告 → **必ず店長・社員に報告**
自己判断は絶対にしない。命に関わります。
"""
        },
        {
            "id": "trouble",
            "title": "トラブル対応",
            "icon": "🚨",
            "content": """
### クレーム対応の基本手順
1. **まず謝罪・傾聴** ——「申し訳ございません」
2. **事実確認** ——何が起きたか落ち着いて聞く
3. **上司に報告** ——必ず店長・社員に伝える
4. **解決策の提示** ——上司指示に従う
5. **記録・共有** ——再発防止のためチームで共有

### NG対応
- その場で言い訳する
- 感情的になる
- 自分だけで解決しようとする

### よくあるケース
| 状況 | 初期対応 |
|------|--------|
| 注文間違い | 即謝罪・店長報告・作り直し |
| 異物混入 | 回収・謝罪・店長報告（廃棄しない） |
| お客様気分不良 | 静かな場所に案内・水を提供・緊急判断 |
| レジミス | 店長確認・丁寧に対応 |

### 緊急連絡
- 火災・救急: **119** / 警察: **110**
- 必ず店長に最初に報告する
"""
        },
        {
            "id": "open_close",
            "title": "開店・閉店の流れ",
            "icon": "🔑",
            "content": """
### 開店前の流れ
1. 出勤・ロッカーでユニフォームに着替え
2. 体調チェック（発熱・下痢・嘔吐がないか）
3. 手洗い・うがい
4. 朝礼・本日の確認事項
5. ホール清掃（テーブル・椅子・床）
6. 備品確認・補充
7. 食材・在庫確認
8. レジ起動・釣り銭確認
9. **開店！**

### 閉店作業の流れ
1. ラストオーダー対応
2. 食材の保管・廃棄処理
3. ホール全体清掃
4. 厨房清掃
5. 食器・調理器具の洗浄・消毒
6. レジ締め
7. ゴミ分別・搬出
8. 消灯・施錠確認
9. 退勤報告

### 鍵のルール
- 開錠・施錠は**必ず責任者と一緒に行う**
- 施錠後は必ず確認（2回まわし）
"""
        },
    ]
}


# ─── ソース量データ（2026年6月4日更新） ────────────────────────
SAUCE_DATA = [
    {
        "rice_g": 100, "label": "100g（お子さまカレー）",
        "pork": 88,  "beef": None, "hayashi_niku": None,          "hayashi_tama": None,
        "tobikara": None,
        "mashi_pork": None, "mashi_beef": None, "mashi_hayashi": None, "tobikara_mashi": None,
        "mashimashi_pork": None, "mashimashi_beef": None, "mashimashi_hayashi": None, "tobikara_mashimashi": None,
        "sara_normal": "スモール皿", "sara_tejikomi": "スモール皿", "sara_mashi": None,
    },
    {
        "rice_g": 150, "label": "150g",
        "pork": 154, "beef": 138, "hayashi_niku": "3～4個(約16g)", "hayashi_tama": 140,
        "tobikara": "0.7杯",
        "mashi_pork": 242, "mashi_beef": 226, "mashi_hayashi": 228, "tobikara_mashi": None,
        "mashimashi_pork": 330, "mashimashi_beef": 314, "mashimashi_hayashi": 316, "tobikara_mashimashi": None,
        "sara_normal": "スモール皿", "sara_tejikomi": "スモール皿またはカレー皿(フチ線あり)", "sara_mashi": "普通皿",
    },
    {
        "rice_g": 200, "label": "200g",
        "pork": 176, "beef": 158, "hayashi_niku": "3～5個(約18g)", "hayashi_tama": 160,
        "tobikara": "0.8杯",
        "mashi_pork": 264, "mashi_beef": 246, "mashi_hayashi": 248, "tobikara_mashi": None,
        "mashimashi_pork": 352, "mashimashi_beef": 334, "mashimashi_hayashi": 336, "tobikara_mashimashi": None,
        "sara_normal": "カレー皿(フチ線あり)", "sara_tejikomi": None, "sara_mashi": "普通皿",
    },
    {
        "rice_g": 250, "label": "250g",
        "pork": 220, "beef": 197, "hayashi_niku": "4～6個(約23g)", "hayashi_tama": 200,
        "tobikara": "1杯（基準）",
        "mashi_pork": 308, "mashi_beef": 285, "mashi_hayashi": 288, "tobikara_mashi": None,
        "mashimashi_pork": 396, "mashimashi_beef": 373, "mashimashi_hayashi": 376, "tobikara_mashimashi": None,
        "sara_normal": "普通皿", "sara_tejikomi": None, "sara_mashi": "中間皿",
    },
    {
        "rice_g": 300, "label": "300g（普通盛）",
        "pork": 220, "beef": 197, "hayashi_niku": "4～6個(約23g)", "hayashi_tama": 200,
        "tobikara": "1杯（基準）",
        "mashi_pork": 308, "mashi_beef": 285, "mashi_hayashi": 288, "tobikara_mashi": None,
        "mashimashi_pork": 396, "mashimashi_beef": 373, "mashimashi_hayashi": 376, "tobikara_mashimashi": None,
        "sara_normal": "普通皿", "sara_tejikomi": None, "sara_mashi": "中間皿",
    },
    {
        "rice_g": 350, "label": "350g",
        "pork": 290, "beef": 262, "hayashi_niku": "5～7個(約28g)", "hayashi_tama": 265,
        "tobikara": "1.3杯",
        "mashi_pork": 378, "mashi_beef": 350, "mashi_hayashi": 353, "tobikara_mashi": None,
        "mashimashi_pork": 466, "mashimashi_beef": 438, "mashimashi_hayashi": 441, "tobikara_mashimashi": None,
        "sara_normal": "普通皿", "sara_tejikomi": None, "sara_mashi": "中間皿",
    },
    {
        "rice_g": 400, "label": "400g",
        "pork": 290, "beef": 262, "hayashi_niku": "5～7個(約28g)", "hayashi_tama": 265,
        "tobikara": "1.3杯",
        "mashi_pork": 378, "mashi_beef": 350, "mashi_hayashi": 353, "tobikara_mashi": None,
        "mashimashi_pork": 466, "mashimashi_beef": 438, "mashimashi_hayashi": 441, "tobikara_mashimashi": None,
        "sara_normal": "普通皿", "sara_tejikomi": None, "sara_mashi": "中間皿",
    },
    {
        "rice_g": 500, "label": "500g",
        "pork": 360, "beef": 328, "hayashi_niku": "6～8個(約32g)", "hayashi_tama": 330,
        "tobikara": "1.6杯",
        "mashi_pork": 448, "mashi_beef": 416, "mashi_hayashi": 418, "tobikara_mashi": None,
        "mashimashi_pork": 536, "mashimashi_beef": 504, "mashimashi_hayashi": 506, "tobikara_mashimashi": None,
        "sara_normal": "中間皿", "sara_tejikomi": None, "sara_mashi": "大皿",
    },
    {
        "rice_g": 600, "label": "600g",
        "pork": 440, "beef": 403, "hayashi_niku": "7～9個(約37g)", "hayashi_tama": 400,
        "tobikara": "2杯",
        "mashi_pork": 528, "mashi_beef": 491, "mashi_hayashi": 488, "tobikara_mashi": "0.4杯",
        "mashimashi_pork": 616, "mashimashi_beef": 579, "mashimashi_hayashi": 576, "tobikara_mashimashi": "0.8杯",
        "sara_normal": None, "sara_tejikomi": None, "sara_mashi": "大皿",
    },
    {
        "rice_g": 700, "label": "700g",
        "pork": 484, "beef": 442, "hayashi_niku": "8～10個(約42g)", "hayashi_tama": 440,
        "tobikara": "2.2杯",
        "mashi_pork": 572, "mashi_beef": 530, "mashi_hayashi": 528, "tobikara_mashi": None,
        "mashimashi_pork": 660, "mashimashi_beef": 618, "mashimashi_hayashi": 616, "tobikara_mashimashi": None,
        "sara_normal": None, "sara_tejikomi": None, "sara_mashi": "大皿",
    },
    {
        "rice_g": 800, "label": "800g",
        "pork": 528, "beef": 482, "hayashi_niku": "9～11個(約46g)", "hayashi_tama": 480,
        "tobikara": "2.4杯",
        "mashi_pork": 616, "mashi_beef": 570, "mashi_hayashi": 568, "tobikara_mashi": None,
        "mashimashi_pork": 704, "mashimashi_beef": 658, "mashimashi_hayashi": 656, "tobikara_mashimashi": None,
        "sara_normal": None, "sara_tejikomi": None, "sara_mashi": "大皿",
    },
    {
        "rice_g": 900, "label": "900g",
        "pork": 572, "beef": 521, "hayashi_niku": "11個(約51g)",   "hayashi_tama": 520,
        "tobikara": "2.6杯",
        "mashi_pork": 660, "mashi_beef": 609, "mashi_hayashi": 608, "tobikara_mashi": None,
        "mashimashi_pork": 748, "mashimashi_beef": 697, "mashimashi_hayashi": 696, "tobikara_mashimashi": None,
        "sara_normal": None, "sara_tejikomi": None, "sara_mashi": "大皿",
    },
    {
        "rice_g": 1000, "label": "1,000g",
        "pork": 650, "beef": 595, "hayashi_niku": "12個(約55g)",   "hayashi_tama": 590,
        "tobikara": "3杯",
        "mashi_pork": 738, "mashi_beef": 683, "mashi_hayashi": 678, "tobikara_mashi": None,
        "mashimashi_pork": 826, "mashimashi_beef": 771, "mashimashi_hayashi": 766, "tobikara_mashimashi": None,
        "sara_normal": "大皿", "sara_tejikomi": "大皿", "sara_mashi": "大皿",
    },
    {
        "rice_g": 1100, "label": "1,100g",
        "pork": 650, "beef": 595, "hayashi_niku": "12個(約55g)",   "hayashi_tama": 590,
        "tobikara": "3杯",
        "mashi_pork": 738, "mashi_beef": 683, "mashi_hayashi": 678, "tobikara_mashi": None,
        "mashimashi_pork": 826, "mashimashi_beef": 771, "mashimashi_hayashi": 766, "tobikara_mashimashi": None,
        "sara_normal": "大皿", "sara_tejikomi": None, "sara_mashi": "大皿",
    },
    {
        "rice_g": 1400, "label": "1,400g",
        "pork": 730, "beef": 670, "hayashi_niku": "13個(約60g)",   "hayashi_tama": 660,
        "tobikara": "3.4杯",
        "mashi_pork": 818, "mashi_beef": 758, "mashi_hayashi": 748, "tobikara_mashi": None,
        "mashimashi_pork": 906, "mashimashi_beef": 846, "mashimashi_hayashi": 836, "tobikara_mashimashi": None,
        "sara_normal": "大皿", "sara_tejikomi": "大皿", "sara_mashi": "大皿",
    },
]

def get_manual():
    data = load_json("manual.json")
    if not data.get("sections"):
        save_json("manual.json", DEFAULT_MANUAL)
        return DEFAULT_MANUAL
    return data


def get_categories(base=None):
    """サブフォルダ名をカテゴリとして取得。ルートにもPDFがあれば先頭に None を含める"""
    if base is None:
        base = PDF_DIR
    if not os.path.exists(base):
        return []
    subs = sorted([
        d for d in os.listdir(base)
        if os.path.isdir(os.path.join(base, d))
    ])
    if not subs:
        return [None]
    # サブフォルダがあっても、ルート直下にPDFが残っていれば先頭に追加
    root_pdfs = [f for f in os.listdir(base) if f.lower().endswith('.pdf')]
    return ([None] if root_pdfs else []) + subs


def get_pdfs_in_category(category, base=None):
    """カテゴリ（サブフォルダ名 or None=ルート）のPDF一覧"""
    if base is None:
        base = PDF_DIR
    folder = base if category is None else os.path.join(base, category)
    if not os.path.exists(folder):
        return []
    return sorted([f for f in os.listdir(folder) if f.lower().endswith('.pdf')])


def clean_curry_name(filename):
    """ファイル名からカレー名を抽出（日付部分を除去）"""
    name = filename.replace('.pdf', '').strip()
    # （2025.12.1～）などの日付を除去
    name = re.sub(r'[\s　]*[（(]\d{4}\.\d+\.\d+[～~][^）)]*[）)]\s*', '', name)
    name = name.strip()
    return name


def _render_pdf_panel(pdfs, folder, key_prefix):
    """検索・ボタングリッド・PDF表示"""
    if not pdfs:
        st.info("このカテゴリにPDFがありません。")
        return

    # 検索
    search_query = st.text_input(
        "🔍 検索",
        placeholder="例: チキン、エビ、カツ、なす...",
        key=f"search_{key_prefix}",
    )
    q = search_query.strip()
    filtered = [
        f for f in pdfs
        if not q or q.lower() in clean_curry_name(f).lower() or q in clean_curry_name(f)
    ]
    st.caption(f"全 {len(pdfs)} 件 / {len(filtered)} 件表示")

    if not filtered:
        st.info("該当するメニューが見つかりません。")
        return

    sel_key = f"sel_{key_prefix}"
    if sel_key not in st.session_state:
        st.session_state[sel_key] = None
    sel = st.session_state[sel_key]
    if sel and sel not in pdfs:
        sel = None
        st.session_state[sel_key] = None

    # ── ボタングリッド（2列固定） ────────────────────────────
    for i in range(0, len(filtered), 2):
        row = filtered[i:i + 2]
        cols = st.columns(2, gap="small")
        for col, fname in zip(cols, row):
            cname  = clean_curry_name(fname)
            is_sel = (sel == fname)
            with col:
                if st.button(
                    ("✅ " if is_sel else "") + cname,
                    key=f"btn_{key_prefix}_{fname}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary",
                ):
                    st.session_state[sel_key] = None if is_sel else fname
                    st.rerun()

    # ── PDF表示 ────────────────────────────────────────────────
    if sel:
        cname = clean_curry_name(sel)
        fpath = os.path.join(folder, sel)
        st.divider()
        c1, c2 = st.columns([5, 1])
        with c1:
            st.markdown(f"**📄 {cname}**")
        with c2:
            if st.button("✖", key=f"close_{key_prefix}", use_container_width=True):
                st.session_state[sel_key] = None
                st.rerun()
        render_pdf_as_images(fpath, key_prefix)


@st.cache_data(show_spinner="PDFを読み込み中...")
def _pdf_to_images(file_path: str) -> list[bytes]:
    """PDFの全ページをPNG画像に変換してキャッシュ"""
    doc = fitz.open(file_path)
    images = []
    for page in doc:
        mat = fitz.Matrix(2.0, 2.0)   # 2倍解像度（鮮明）
        pix = page.get_pixmap(matrix=mat)
        images.append(pix.tobytes("png"))
    doc.close()
    return images


def render_pdf_as_images(file_path: str, key_prefix: str = ""):
    """PDFをページ画像として表示（スマホ・PC共通）"""
    images = _pdf_to_images(file_path)
    total = len(images)

    if total == 0:
        st.error("PDFを読み込めませんでした。")
        return

    # ページナビ（複数ページの場合）
    page_key = f"page_{key_prefix}_{os.path.basename(file_path)}"
    if page_key not in st.session_state:
        st.session_state[page_key] = 0
    page_idx = st.session_state[page_key]

    if total > 1:
        nav1, nav2, nav3 = st.columns([1, 3, 1])
        with nav1:
            if st.button("◀", key=f"prev_{key_prefix}", disabled=(page_idx == 0),
                         use_container_width=True):
                st.session_state[page_key] = page_idx - 1
                st.rerun()
        with nav2:
            st.markdown(
                f"<div style='text-align:center;padding:6px 0;font-weight:600;'>"
                f"{page_idx + 1} / {total} ページ</div>",
                unsafe_allow_html=True,
            )
        with nav3:
            if st.button("▶", key=f"next_{key_prefix}", disabled=(page_idx == total - 1),
                         use_container_width=True):
                st.session_state[page_key] = page_idx + 1
                st.rerun()

    # 画像表示
    st.image(images[page_idx], use_container_width=True)

    # ダウンロードボタン（念のため）
    with open(file_path, "rb") as f:
        st.download_button(
            "📥 PDFをダウンロード",
            data=f.read(),
            file_name=os.path.basename(file_path),
            mime="application/pdf",
            use_container_width=True,
            key=f"dl_{key_prefix}_{os.path.basename(file_path)}",
        )


# ─── ページヘッダー ──────────────────────────────────────────
page_header("📋 マニュアル", "業務ルール & カレーマニュアル")

tab_curry, tab_general, tab_sauce, tab_teisu = st.tabs([
    "カレーマニュアル", "業務マニュアル", "ソース量表", "定数表"
])


# ══════════════════════════════════════════════════════════════
# TAB 1: カレーマニュアル（PDF表示）
# ══════════════════════════════════════════════════════════════
with tab_curry:
    # フォルダが存在しなければ作成
    for folder_name, _ in MANUAL_FOLDERS:
        os.makedirs(os.path.join(BASE_DIR, folder_name), exist_ok=True)

    # ── 管理者: PDF管理パネル ────────────────────────────────
    if is_manager(user):
        with st.expander("⚙️ PDF管理（管理者・代行）", expanded=False):

            # 操作対象フォルダ選択
            st.markdown("#### 🗂️ 操作対象フォルダ")
            mgmt_folder_label = st.selectbox(
                "フォルダを選択",
                options=[label for _, label in MANUAL_FOLDERS],
                key="mgmt_folder_sel",
            )
            mgmt_folder_name = next(n for n, l in MANUAL_FOLDERS if l == mgmt_folder_label)
            mgmt_base = os.path.join(BASE_DIR, mgmt_folder_name)
            mgmt_cats = get_categories(mgmt_base)

            st.divider()

            # カテゴリ（サブフォルダ）管理
            st.markdown("#### 📁 カテゴリ管理")
            st.caption("サブフォルダがカテゴリとして表示されます。")
            new_cat = st.text_input("新しいカテゴリ名", placeholder="例: 期間限定、定番", key="new_cat_input")
            if st.button("＋ カテゴリ作成", key="create_cat"):
                if new_cat.strip():
                    os.makedirs(os.path.join(mgmt_base, new_cat.strip()), exist_ok=True)
                    st.success(f"「{new_cat.strip()}」を作成しました。")
                    st.rerun()
                else:
                    st.warning("カテゴリ名を入力してください。")

            st.divider()

            # PDFアップロード
            st.markdown("#### 📤 PDFアップロード")
            st.caption("同じファイル名で上書きすると内容が更新されます。")
            all_cats_u = [c for c in mgmt_cats if c is not None]
            if all_cats_u:
                upload_target = st.selectbox(
                    "アップロード先カテゴリ",
                    options=["（ルート）"] + all_cats_u,
                    key="upload_target",
                )
                target_folder = mgmt_base if upload_target == "（ルート）" else os.path.join(mgmt_base, upload_target)
            else:
                upload_target = "（ルート）"
                target_folder = mgmt_base

            uploaded = st.file_uploader(
                "PDFファイルを選択（複数可）",
                type="pdf",
                accept_multiple_files=True,
                key="pdf_uploader",
            )
            if uploaded:
                if st.button("💾 アップロード実行", type="primary"):
                    os.makedirs(target_folder, exist_ok=True)
                    saved = []
                    for f in uploaded:
                        with open(os.path.join(target_folder, f.name), "wb") as out:
                            out.write(f.getbuffer())
                        saved.append(clean_curry_name(f.name))
                    st.success(f"✅ {upload_target} に {len(saved)} 件追加：{', '.join(saved)}")
                    st.rerun()

            st.divider()

            # PDF移動
            st.markdown("#### 🔀 PDFを別カテゴリへ移動")
            st.caption("同フォルダ内での移動です。フォルダをまたぐ移動はできません。")
            all_cats_mv = ([None] if get_pdfs_in_category(None, mgmt_base) else []) + [c for c in mgmt_cats if c is not None]
            all_labels_mv = ["（ルート）" if c is None else c for c in all_cats_mv]

            if len(all_cats_mv) < 2:
                st.info("移動先カテゴリがありません。先にカテゴリを作成してください。")
            else:
                mv_src_label = st.selectbox("移動元カテゴリ", all_labels_mv, key="mv_src")
                mv_src_cat   = None if mv_src_label == "（ルート）" else mv_src_label
                mv_src_pdfs  = get_pdfs_in_category(mv_src_cat, mgmt_base)
                if mv_src_pdfs:
                    mv_pdf = st.selectbox("移動するPDF", mv_src_pdfs, format_func=clean_curry_name, key="mv_pdf")
                    dst_opts = [l for l in all_labels_mv if l != mv_src_label]
                    mv_dst_label = st.selectbox("移動先カテゴリ", dst_opts, key="mv_dst")
                    mv_dst_cat   = None if mv_dst_label == "（ルート）" else mv_dst_label
                    if st.button("🔀 移動実行", key="mv_exec", type="primary"):
                        src_f = mgmt_base if mv_src_cat is None else os.path.join(mgmt_base, mv_src_cat)
                        dst_f = mgmt_base if mv_dst_cat is None else os.path.join(mgmt_base, mv_dst_cat)
                        os.makedirs(dst_f, exist_ok=True)
                        os.rename(os.path.join(src_f, mv_pdf), os.path.join(dst_f, mv_pdf))
                        st.success(f"「{clean_curry_name(mv_pdf)}」を「{mv_dst_label}」へ移動しました。")
                        st.rerun()
                else:
                    st.info("このカテゴリにPDFがありません。")

            st.divider()

            # カテゴリ削除
            st.markdown("#### 🗂️ カテゴリ削除")
            st.caption("空のカテゴリのみ削除できます。")
            deletable_cats = [c for c in mgmt_cats if c is not None and not get_pdfs_in_category(c, mgmt_base)]
            if deletable_cats:
                del_cat_sel = st.selectbox("削除するカテゴリ", deletable_cats, key="del_cat_sel")
                if st.button("🗑️ カテゴリ削除", key="del_cat_exec"):
                    try:
                        os.rmdir(os.path.join(mgmt_base, del_cat_sel))
                        st.success(f"「{del_cat_sel}」を削除しました。")
                        st.rerun()
                    except Exception as e:
                        st.error(f"削除に失敗しました: {e}")
            else:
                st.info("削除できる空のカテゴリがありません。")

            st.divider()

            # PDF削除
            st.markdown("#### 🗑️ PDF削除")
            st.caption("削除ボタンを押すと確認メッセージが表示されます。")
            all_cats_del = ([None] if get_pdfs_in_category(None, mgmt_base) else []) + [c for c in mgmt_cats if c is not None]
            for cat in all_cats_del:
                cat_label = "ルート" if cat is None else cat
                cat_pdfs  = get_pdfs_in_category(cat, mgmt_base)
                if not cat_pdfs:
                    continue
                st.markdown(f"**📁 {cat_label}**")
                del_cols = st.columns(2)
                for i, fname in enumerate(cat_pdfs):
                    cname = clean_curry_name(fname)
                    pending_key = f"pending_del_{mgmt_folder_name}_{cat}_{fname}"
                    fpath = os.path.join(mgmt_base if cat is None else os.path.join(mgmt_base, cat), fname)
                    with del_cols[i % 2]:
                        dc1, dc2 = st.columns([4, 1])
                        with dc1:
                            st.markdown(f"📄 {cname}")
                        with dc2:
                            if not st.session_state.get(pending_key):
                                if st.button("🗑️", key=f"del_{mgmt_folder_name}_{cat}_{fname}", help=f"{cname}を削除"):
                                    st.session_state[pending_key] = True
                                    st.rerun()
                    # 確認プロンプト（列の外に出して見やすく）
                    if st.session_state.get(pending_key):
                        st.warning(f"⚠️ 「{cname}」を本当に削除しますか？この操作は取り消せません。")
                        cf1, cf2 = st.columns(2)
                        with cf1:
                            if st.button("✅ 削除する", key=f"confirm_del_{mgmt_folder_name}_{cat}_{fname}", type="primary"):
                                os.remove(fpath)
                                st.session_state.pop(pending_key, None)
                                st.success(f"「{cname}」を削除しました。")
                                st.rerun()
                        with cf2:
                            if st.button("❌ キャンセル", key=f"cancel_del_{mgmt_folder_name}_{cat}_{fname}"):
                                st.session_state.pop(pending_key, None)
                                st.rerun()

    # ── メインフォルダをタブで切り替え ─────────────────────────
    existing_folders = [(n, l) for n, l in MANUAL_FOLDERS if os.path.exists(os.path.join(BASE_DIR, n))]
    if not existing_folders:
        st.info("マニュアルフォルダが見つかりません。")
    else:
        main_tabs = st.tabs([label for _, label in existing_folders])
        for tab_obj, (folder_name, folder_label) in zip(main_tabs, existing_folders):
            base = os.path.join(BASE_DIR, folder_name)
            cats = get_categories(base)
            with tab_obj:
                cat_labels = ["📄 すべて" if c is None else f"📁 {c}" for c in cats]
                if len(cats) == 1 and cats[0] is None:
                    # サブフォルダなし → そのまま表示
                    _render_pdf_panel(get_pdfs_in_category(None, base), base, folder_name)
                else:
                    cat_tabs = st.tabs(cat_labels)
                    for ctab, cat in zip(cat_tabs, cats):
                        with ctab:
                            folder = base if cat is None else os.path.join(base, cat)
                            _render_pdf_panel(get_pdfs_in_category(cat, base), folder, f"{folder_name}_{cat}")


# ══════════════════════════════════════════════════════════════
# TAB 2: 業務マニュアル（既読トラッキング付き）
# ══════════════════════════════════════════════════════════════
with tab_general:
    manual = get_manual()
    sections = manual.get("sections", [])

    # 管理者・代行: 編集モードトグル
    edit_mode = False
    if is_manager(user):
        edit_mode = st.toggle("✏️ 編集モード（管理者・代行）", value=False)
        if edit_mode:
            st.info("セクションの追加・編集・削除、写真・動画のアップロードができます。")
            if st.button(
                "🔄 デフォルト内容に戻す",
                help="現在の内容を削除してデフォルトデータに戻します",
                type="secondary",
            ):
                save_json("manual.json", DEFAULT_MANUAL)
                st.success("✅ デフォルトデータに戻しました！")
                st.rerun()

    if edit_mode:
        tab_edit, tab_add = st.tabs(["📝 編集", "➕ セクション追加"])

        with tab_edit:
            for i, sec in enumerate(sections):
                with st.expander(f"{sec['icon']} {sec['title']}", expanded=False):
                    new_title   = st.text_input("タイトル", value=sec["title"], key=f"title_{i}")
                    new_icon    = st.text_input("アイコン（絵文字）", value=sec["icon"], key=f"icon_{i}")
                    new_content = st.text_area("内容（Markdown）", value=sec["content"], height=300, key=f"content_{i}")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if st.button("💾 保存", key=f"save_{i}", type="primary"):
                            sections[i]["title"]   = new_title
                            sections[i]["icon"]    = new_icon
                            sections[i]["content"] = new_content
                            manual["sections"] = sections
                            save_json("manual.json", manual)
                            st.success("保存しました！")
                            st.rerun()
                    with col2:
                        if st.button("🗑️ 削除", key=f"del_{i}"):
                            sections.pop(i)
                            manual["sections"] = sections
                            save_json("manual.json", manual)
                            st.warning("削除しました。")
                            st.rerun()
                    st.divider()
                    st.markdown("**📎 添付ファイル管理**")
                    render_attachments("manual", sec["id"], allow_delete=True)
                    upload_attachment_ui("manual", sec["id"], "写真・動画・ファイルをアップロード")

        with tab_add:
            with st.form("add_section"):
                st.markdown("#### 新しいセクションを追加")
                new_icon    = st.text_input("アイコン（絵文字）", value="📌")
                new_title   = st.text_input("タイトル")
                new_content = st.text_area("内容（Markdown）", height=200, placeholder="Markdown形式で入力してください")
                if st.form_submit_button("追加する", type="primary"):
                    if new_title and new_content:
                        import uuid
                        sections.append({
                            "id":      str(uuid.uuid4())[:8],
                            "title":   new_title,
                            "icon":    new_icon,
                            "content": new_content,
                        })
                        manual["sections"] = sections
                        save_json("manual.json", manual)
                        st.success(f"「{new_title}」を追加しました！")
                        st.rerun()
                    else:
                        st.error("タイトルと内容を入力してください。")

    else:
        # 通常表示（既読トラッキング）
        progress     = get_progress(username := user["username"])
        read_sections = set(progress.get("manual_read", []))

        st.caption(f"既読: {len(read_sections)}/{len(sections)} セクション")
        st.progress(len(read_sections) / max(len(sections), 1))
        st.write("")

        for sec in sections:
            sec_id  = sec["id"]
            is_read = sec_id in read_sections
            label   = f"{sec['icon']} {sec['title']} {'✅' if is_read else ''}"
            with st.expander(label, expanded=False):
                st.markdown(sec["content"])
                render_attachments("manual", sec_id)
                if not is_read:
                    if st.button("✅ 読んだ！", key=f"read_{sec_id}", type="primary"):
                        read_sections.add(sec_id)
                        progress["manual_read"] = list(read_sections)
                        save_progress(username, progress)
                        _, new_stamps = award_stamps(username)
                        show_new_stamps(new_stamps)
                        st.rerun()
                else:
                    st.success("既読済み ✅")


# ══════════════════════════════════════════════════════════════
# TAB 3: ソース量表
# ══════════════════════════════════════════════════════════════
with tab_sauce:
    import pandas as pd

    st.markdown("#### ソース量・とび辛スプーン早見表")
    st.caption("ライス量を選択すると各ソース量が表示されます。（2026年6月4日更新）")

    def _fmt(v, unit="g"):
        return f"{v}{unit}" if v is not None else "—"

    rice_labels = [r["label"] for r in SAUCE_DATA]
    default_idx = next((i for i, r in enumerate(SAUCE_DATA) if r["rice_g"] == 300), 0)
    selected_label = st.selectbox("ライス量", rice_labels, index=default_idx)
    row = next(r for r in SAUCE_DATA if r["label"] == selected_label)

    st.divider()

    # ── 3列カード表示 ─────────────────────────────────────────
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            "<div style='background:#fff5f0;border-left:4px solid #e85d04;"
            "padding:10px 14px;border-radius:0 8px 8px 0;margin-bottom:10px;'>"
            "<b style='color:#e85d04;'>通常</b></div>",
            unsafe_allow_html=True,
        )
        st.metric("ポーク・甘口・ベジ", _fmt(row["pork"]))
        st.metric("ビーフ",             _fmt(row["beef"]))
        st.metric("ハヤシ肉",           row["hayashi_niku"] or "—")
        st.metric("ハヤシ玉ねぎ",       _fmt(row["hayashi_tama"]))
        st.metric("とび辛スプーン",     row["tobikara"] or "—")

    with col2:
        st.markdown(
            "<div style='background:#fff0f5;border-left:4px solid #c0392b;"
            "padding:10px 14px;border-radius:0 8px 8px 0;margin-bottom:10px;'>"
            "<b style='color:#c0392b;'>ソース増し</b></div>",
            unsafe_allow_html=True,
        )
        st.metric("ポーク・甘口・ベジ", _fmt(row["mashi_pork"]))
        st.metric("ビーフ",             _fmt(row["mashi_beef"]))
        st.metric("ハヤシ",             _fmt(row["mashi_hayashi"]))
        if row["tobikara_mashi"]:
            st.metric("とび辛（追加分）", row["tobikara_mashi"])

    with col3:
        st.markdown(
            "<div style='background:#f0f5ff;border-left:4px solid #2980b9;"
            "padding:10px 14px;border-radius:0 8px 8px 0;margin-bottom:10px;'>"
            "<b style='color:#2980b9;'>ソース増し増し</b></div>",
            unsafe_allow_html=True,
        )
        st.metric("ポーク・甘口・ベジ", _fmt(row["mashimashi_pork"]))
        st.metric("ビーフ",             _fmt(row["mashimashi_beef"]))
        st.metric("ハヤシ",             _fmt(row["mashimashi_hayashi"]))
        if row["tobikara_mashimashi"]:
            st.metric("とび辛（追加分）", row["tobikara_mashimashi"])

    # ── 使用皿 ───────────────────────────────────────────────
    st.divider()
    sara_parts = []
    if row["sara_normal"]:   sara_parts.append(f"通常: **{row['sara_normal']}**")
    if row["sara_tejikomi"]: sara_parts.append(f"手仕込: **{row['sara_tejikomi']}**")
    if row["sara_mashi"]:    sara_parts.append(f"ソース増し: **{row['sara_mashi']}**")
    if sara_parts:
        st.markdown("使用皿 — " + "　／　".join(sara_parts))
    else:
        st.markdown("使用皿 — （要確認）")

    # ── 全データ一覧 ─────────────────────────────────────────
    st.divider()
    with st.expander("全データ一覧表を表示"):
        df_sauce = pd.DataFrame([{
            "ライス量":           r["label"],
            "ポーク系(g)":       r["pork"]          or "—",
            "ビーフ(g)":         r["beef"]          or "—",
            "ハヤシ肉":          r["hayashi_niku"]  or "—",
            "ハヤシ玉(g)":       r["hayashi_tama"]  or "—",
            "とび辛":            r["tobikara"]      or "—",
            "増し[ポーク系](g)": r["mashi_pork"]    or "—",
            "増し[ビーフ](g)":   r["mashi_beef"]    or "—",
            "増し[ハヤシ](g)":   r["mashi_hayashi"] or "—",
            "増し増し[ポーク](g)":r["mashimashi_pork"]    or "—",
            "増し増し[ビーフ](g)":r["mashimashi_beef"]    or "—",
            "増し増し[ハヤシ](g)":r["mashimashi_hayashi"] or "—",
            "皿(通常)":          r["sara_normal"]   or "—",
            "皿(ソース増し)":    r["sara_mashi"]    or "—",
        } for r in SAUCE_DATA])
        st.dataframe(df_sauce, use_container_width=True, hide_index=True)

    st.caption("※ ソース量の誤差は各規定量の+10g以内とする。")


# ══════════════════════════════════════════════════════════════
# TAB 4: 定数表
# ══════════════════════════════════════════════════════════════
with tab_teisu:
    import pandas as pd

    st.markdown("#### 定数表")
    st.caption("仕込みや発注の定数を自由に記録・管理できます。行は「＋」ボタンで追加、保存ボタンで確定されます。")

    def get_teisu():
        data = load_json("teisu_table.json", {})
        if not data.get("columns"):
            return {"columns": ["品目", "規定量", "単位", "備考"], "rows": []}
        return data

    teisu     = get_teisu()
    t_columns = teisu.get("columns", ["品目", "規定量", "単位", "備考"])
    t_rows    = teisu.get("rows", [])

    # ── 管理者: 列の追加・削除 ──────────────────────────────
    if is_manager(user):
        with st.expander("列の管理（管理者）"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**列を追加**")
                new_col_name = st.text_input("列名", key="teisu_new_col")
                if st.button("追加", key="teisu_add_col", type="primary"):
                    if new_col_name and new_col_name not in t_columns:
                        t_columns.append(new_col_name)
                        for r in t_rows:
                            r.setdefault(new_col_name, "")
                        save_json("teisu_table.json", {"columns": t_columns, "rows": t_rows})
                        st.success(f"「{new_col_name}」列を追加しました。")
                        st.rerun()
                    elif new_col_name in t_columns:
                        st.warning("同じ列名がすでにあります。")
            with col_b:
                st.markdown("**列を削除**")
                if len(t_columns) > 1:
                    del_col_name = st.selectbox("削除する列", t_columns, key="teisu_del_col")
                    if st.button("削除", key="teisu_del_col_btn"):
                        t_columns = [c for c in t_columns if c != del_col_name]
                        for r in t_rows:
                            r.pop(del_col_name, None)
                        save_json("teisu_table.json", {"columns": t_columns, "rows": t_rows})
                        st.success(f"「{del_col_name}」列を削除しました。")
                        st.rerun()
                else:
                    st.info("最低1列は必要です。")

    # ── テーブル表示 ────────────────────────────────────────
    if t_rows:
        df_teisu = pd.DataFrame(t_rows, columns=t_columns)
        for c in t_columns:
            if c not in df_teisu.columns:
                df_teisu[c] = ""
        df_teisu = df_teisu[t_columns]
    else:
        df_teisu = pd.DataFrame(columns=t_columns)

    can_edit = role not in ("kenshu", "new")

    if can_edit:
        edited = st.data_editor(
            df_teisu,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(c, width="medium") for c in t_columns},
            key="teisu_editor",
        )
        if st.button("保存", type="primary", key="teisu_save"):
            new_rows = [
                row for row in edited.to_dict("records")
                if any(str(v).strip() for v in row.values())
            ]
            save_json("teisu_table.json", {"columns": t_columns, "rows": new_rows})
            st.success("保存しました！")
            st.rerun()
    else:
        st.caption("※ 閲覧のみ（編集はメイト以上）")
        st.dataframe(
            df_teisu,
            use_container_width=True,
            hide_index=True,
        )
