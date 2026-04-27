import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import (apply_theme, require_login, page_header, load_json, save_json,
                   get_progress, save_progress, award_stamps, show_new_stamps,
                   is_manager, render_attachments, upload_attachment_ui)

apply_theme()
require_login()

user = st.session_state.user
role = user.get("role", "new")

# ─── デフォルトマニュアルデータ ──────────────────────────────
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

# ─── ページ ──────────────────────────────────────────────────
page_header("📋 マニュアル", "業務内容・ルールを確認しよう")

manual = get_manual()
sections = manual.get("sections", [])

# 管理者・代行: 編集モードトグル
edit_mode = False
if is_manager(user):
    edit_mode = st.toggle("✏️ 編集モード（管理者・代行）", value=False)
    if edit_mode:
        st.info("セクションの追加・編集・削除、写真・動画のアップロードができます。")

# ─── セクション一覧 ──────────────────────────────────────────
if edit_mode:
    # 管理者編集UI
    tab_view, tab_add = st.tabs(["📝 編集", "➕ セクション追加"])

    with tab_view:
        for i, sec in enumerate(sections):
            with st.expander(f"{sec['icon']} {sec['title']}", expanded=False):
                new_title = st.text_input("タイトル", value=sec["title"], key=f"title_{i}")
                new_icon = st.text_input("アイコン（絵文字）", value=sec["icon"], key=f"icon_{i}")
                new_content = st.text_area("内容（Markdown）", value=sec["content"], height=300, key=f"content_{i}")
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button("💾 保存", key=f"save_{i}", type="primary"):
                        sections[i]["title"] = new_title
                        sections[i]["icon"] = new_icon
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
            new_icon = st.text_input("アイコン（絵文字）", value="📌")
            new_title = st.text_input("タイトル")
            new_content = st.text_area("内容（Markdown）", height=200, placeholder="Markdown形式で入力してください")
            if st.form_submit_button("追加する", type="primary"):
                if new_title and new_content:
                    import uuid
                    sections.append({
                        "id": str(uuid.uuid4())[:8],
                        "title": new_title,
                        "icon": new_icon,
                        "content": new_content,
                    })
                    manual["sections"] = sections
                    save_json("manual.json", manual)
                    st.success(f"「{new_title}」を追加しました！")
                    st.rerun()
                else:
                    st.error("タイトルと内容を入力してください。")
else:
    # 通常表示
    progress = get_progress(username := user["username"])
    read_sections = set(progress.get("manual_read", []))

    st.caption(f"既読: {len(read_sections)}/{len(sections)} セクション")
    st.progress(len(read_sections) / max(len(sections), 1))
    st.write("")

    for sec in sections:
        sec_id = sec["id"]
        is_read = sec_id in read_sections
        label = f"{sec['icon']} {sec['title']} {'✅' if is_read else ''}"
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
