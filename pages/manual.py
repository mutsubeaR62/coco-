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

tab_curry, tab_general = st.tabs(["🍛 カレーマニュアル", "📖 業務マニュアル"])


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
