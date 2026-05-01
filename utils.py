import json
import hashlib
import os
import streamlit as st
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")

# ─── テーマCSS ─────────────────────────────────────────────────
THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }

/* ══ サイドバー ══════════════════════════════════════════════
   config.toml で secondaryBackgroundColor = "#fff3e0" を設定済み。
   ここでは文字色・アクセントカラーのみ上書きする。
*/
[data-testid="stSidebar"] {
    border-right: 2px solid #e85d04;
}
section[data-testid="stSidebar"] > div { padding-top: 0.5rem; }

/* サイドバー内の全テキストを確実に濃い色にする */
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] a,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] div {
    color: #1a1a1a !important;
}

/* ナビゲーションリンク */
[data-testid="stSidebar"] a {
    color: #333333 !important;
    border-radius: 8px;
    font-weight: 500 !important;
    transition: all 0.15s;
}
[data-testid="stSidebar"] a:hover {
    color: #e85d04 !important;
    background: rgba(232,93,4,0.10) !important;
}
[data-testid="stSidebar"] a[aria-selected="true"] {
    color: #ffffff !important;
    background: linear-gradient(90deg, #e85d04, #f48c06) !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px rgba(232,93,4,0.35);
}

/* ══ レスポンシブ対応 ═════════════════════════════════════════ */

/* タブレット (〜1024px) */
@media (max-width: 1024px) {
    .page-header h1 { font-size: 1.3rem !important; }
    .page-header p  { font-size: 0.82rem !important; }
    .info-card { padding: 14px 16px !important; }
    .stamp-circle { width: 60px !important; height: 60px !important; font-size: 1.6rem !important; }
    .stamp-item { width: 76px !important; }
}

/* スマホ (〜767px) */
@media (max-width: 767px) {
    /* メインコンテンツの余白を縮める */
    .main .block-container {
        padding: 0.8rem 0.6rem 2rem !important;
        max-width: 100% !important;
    }

    /* iOS でのテキスト自動ズームを防ぐ（16px未満だとズームされる） */
    input, textarea, select {
        font-size: 16px !important;
    }

    /* ページヘッダー */
    .page-header { padding: 12px 14px !important; border-radius: 10px !important; margin-bottom: 14px !important; }
    .page-header h1 { font-size: 1.05rem !important; }
    .page-header p  { font-size: 0.75rem !important; }

    /* カラムを折り返す（2列グリッド） */
    [data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
        gap: 6px !important;
    }
    [data-testid="stHorizontalBlock"] > [data-testid="column"] {
        min-width: calc(50% - 6px) !important;
        flex: 1 1 calc(50% - 6px) !important;
        width: calc(50% - 6px) !important;
    }

    /* ボタンはタッチしやすいサイズ */
    .stButton > button {
        min-height: 44px !important;
        font-size: 0.9rem !important;
        padding: 8px 12px !important;
    }

    /* カード */
    .info-card { padding: 10px 12px !important; border-radius: 10px !important; }
    .metric-card { padding: 12px 8px !important; }
    .metric-value { font-size: 1.5rem !important; }

    /* スタンプ */
    .stamp-grid { gap: 8px !important; }
    .stamp-circle { width: 50px !important; height: 50px !important; font-size: 1.3rem !important; }
    .stamp-item { width: 62px !important; }
    .stamp-name { font-size: 0.58rem !important; }

    /* フラッシュカード */
    .flashcard { padding: 24px 14px !important; min-height: 130px !important; }
    .flashcard .fc-text { font-size: 1.1rem !important; }

    /* なぜやるか */
    .why-box { font-size: 0.78rem !important; margin-left: 10px !important; }

    /* タブのラベルを小さく */
    [data-testid="stTabs"] button { font-size: 0.8rem !important; padding: 6px 10px !important; }

    /* テーブルのスクロール */
    [data-testid="stDataFrame"], .stbl, .shift-tbl {
        overflow-x: auto !important;
        display: block !important;
    }

    /* メトリクス行 */
    [data-testid="stMetric"] { padding: 8px !important; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.7rem !important; }

    /* サイドバーユーザーカード */
    .sidebar-user { padding: 10px 12px !important; }
    .sidebar-user .name { font-size: 0.95rem !important; }
}


/* Page header */
.page-header {
    background: linear-gradient(135deg, #e85d04 0%, #f48c06 100%);
    color: white; padding: 18px 24px; border-radius: 14px;
    margin-bottom: 24px; box-shadow: 0 4px 16px rgba(232,93,4,0.3);
}
.page-header h1 { margin: 0; font-size: 1.6rem; font-weight: 700; }
.page-header p  { margin: 4px 0 0; font-size: 0.9rem; opacity: 0.85; }

/* Cards */
.info-card {
    background: white; border-radius: 14px; padding: 20px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07); margin: 8px 0;
    border-left: 4px solid #e85d04; transition: box-shadow 0.2s;
}
.info-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.12); }
.info-card-neutral { border-left: 4px solid #6c757d; }
.info-card-green   { border-left: 4px solid #28a745; }
.info-card-blue    { border-left: 4px solid #007bff; }

/* Metric cards */
.metric-row { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.metric-card {
    flex: 1; min-width: 120px; background: white; border-radius: 12px;
    padding: 16px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.07);
}
.metric-value { font-size: 2rem; font-weight: 700; color: #e85d04; }
.metric-label { font-size: 0.8rem; color: #666; margin-top: 4px; }

/* Stamp system */
.stamp-grid { display: flex; flex-wrap: wrap; gap: 16px; padding: 8px 0; }
.stamp-item { text-align: center; width: 90px; cursor: default; }
.stamp-circle {
    width: 72px; height: 72px; border-radius: 50%; margin: 0 auto 6px;
    display: flex; align-items: center; justify-content: center;
    font-size: 2rem;
    background: linear-gradient(135deg, #e85d04, #f48c06);
    box-shadow: 0 4px 14px rgba(232,93,4,0.4);
    transition: transform 0.2s;
}
.stamp-circle:hover { transform: scale(1.1); }
.stamp-circle.locked {
    background: #e0e0e0;
    box-shadow: none;
    filter: grayscale(1);
    opacity: 0.4;
}
.stamp-name { font-size: 0.7rem; font-weight: 700; color: #333; }
.stamp-name.locked { color: #aaa; }

/* Why box (checklist) */
.why-box {
    background: #fff8f0; border-left: 3px solid #f48c06;
    padding: 8px 12px; border-radius: 0 8px 8px 0;
    font-size: 0.82rem; color: #555; margin: 4px 0 12px 28px;
    line-height: 1.5;
}

/* Flashcard */
.flashcard {
    border-radius: 18px; padding: 40px 30px;
    text-align: center; min-height: 180px;
    display: flex; align-items: center; justify-content: center;
    flex-direction: column; margin: 16px 0;
    box-shadow: 0 8px 28px rgba(0,0,0,0.12);
    transition: all 0.3s;
}
.flashcard-front { background: linear-gradient(135deg, #e85d04, #f48c06); color: white; }
.flashcard-back  { background: linear-gradient(135deg, #1b4332, #2d6a4f); color: white; }
.flashcard .fc-label { font-size: 0.85rem; opacity: 0.7; margin-bottom: 12px; }
.flashcard .fc-text  { font-size: 1.6rem; font-weight: 700; line-height: 1.4; }

/* Quiz */
.quiz-result-correct { background: #d4edda; border: 2px solid #28a745; border-radius: 10px; padding: 12px 16px; margin: 8px 0; }
.quiz-result-wrong   { background: #f8d7da; border: 2px solid #dc3545; border-radius: 10px; padding: 12px 16px; margin: 8px 0; }

/* User info sidebar */
.sidebar-user {
    background: rgba(232,93,4,0.12); border-radius: 10px;
    padding: 14px 16px; margin: 8px 8px 4px;
    border: 1px solid rgba(232,93,4,0.35);
}
.sidebar-user .name { color: #1a1a1a !important; font-weight: 700; font-size: 1.05rem; }
.sidebar-user .role { color: #c44e00 !important; font-size: 0.82rem; margin-top: 3px; font-weight: 600; }

/* General */
.stButton > button { border-radius: 10px !important; font-weight: 600 !important; transition: all 0.2s !important; }
.stButton > button[kind="primary"] { background: linear-gradient(135deg, #e85d04, #f48c06) !important; border: none !important; }
.stButton > button[kind="primary"]:hover { box-shadow: 0 4px 12px rgba(232,93,4,0.4) !important; transform: translateY(-1px) !important; }
div[data-testid="stProgress"] > div > div > div { background: linear-gradient(90deg, #e85d04, #f48c06) !important; }
</style>
"""

# ─── スタンプ定義 ──────────────────────────────────────────────
STAMPS = {
    "first_login":    {"emoji": "🌟", "name": "はじめの一歩", "desc": "初めてログイン！これからよろしく！"},
    "manual_reader":  {"emoji": "📚", "name": "マニュアル読破", "desc": "マニュアルを3セクション以上読んだ"},
    "quiz_pass":      {"emoji": "🎯", "name": "クイズ合格",    "desc": "クイズで70%以上を達成"},
    "quiz_perfect":   {"emoji": "💯", "name": "満点マスター",  "desc": "クイズで全問正解！"},
    "opening_master": {"emoji": "🌅", "name": "開店マスター",  "desc": "開店チェックを3回完了"},
    "closing_master": {"emoji": "🌙", "name": "閉店マスター",  "desc": "閉店チェックを3回完了"},
    "hygiene_master": {"emoji": "🧼", "name": "衛生マスター",  "desc": "衛生チェックを5回完了"},
    "service_pro":    {"emoji": "👑", "name": "接客プロ",      "desc": "接客チェックを5回完了"},
    "order_master":   {"emoji": "📦", "name": "発注マスター",  "desc": "発注を10回完了"},
    "all_star":       {"emoji": "🏆", "name": "CoCo一番星",   "desc": "他のスタンプを7つ以上獲得"},
}

ROLE_LABELS = {
    "admin":  "👑 管理者",
    "daiko":  "🔑 代行",
    "mate":   "🏪 メイト",
    "kenshu": "🌱 研修",
    # 旧ロール互換
    "staff": "🏪 メイト",
    "new":   "🌱 研修",
}

def is_manager(user):
    """管理者または代行かどうか。"""
    return user.get("role") in ("admin", "daiko")

# ─── データ管理 ───────────────────────────────────────────────
def _ensure_data():
    os.makedirs(DATA_DIR, exist_ok=True)

@st.cache_resource
def _get_supabase():
    try:
        from supabase import create_client
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception:
        return None

def load_json(filename, default=None):
    sb = _get_supabase()
    if sb:
        try:
            result = sb.table("json_store").select("data").eq("key", filename).execute()
            if result.data:
                return result.data[0]["data"]
            return default if default is not None else {}
        except Exception:
            pass
    # フォールバック: ローカルファイル
    _ensure_data()
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return default if default is not None else {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def save_json(filename, data):
    sb = _get_supabase()
    if sb:
        try:
            sb.table("json_store").upsert({"key": filename, "data": data}).execute()
            return
        except Exception:
            pass
    # フォールバック: ローカルファイル
    _ensure_data()
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── ユーザー管理 ─────────────────────────────────────────────
def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_default_users():
    data = load_json("users.json", {"users": []})
    if not data.get("users"):
        defaults = [
            {"username": "manager",  "password": _hash("coco1234"), "name": "店長",      "role": "admin", "joined": "2020-04-01"},
            {"username": "staff1",   "password": _hash("coco1234"), "name": "先輩スタッフ","role": "staff", "joined": "2023-04-01"},
            {"username": "new1",     "password": _hash("coco1234"), "name": "新人さん",    "role": "new",   "joined": datetime.now().strftime("%Y-%m-%d")},
        ]
        save_json("users.json", {"users": defaults})

def login_user(username, password):
    users = load_json("users.json", {"users": []}).get("users", [])
    hashed = _hash(password)
    for u in users:
        if u["username"] == username and u["password"] == hashed:
            return u
    return None

def get_all_users():
    return load_json("users.json", {"users": []}).get("users", [])

def get_user_by_username(username):
    for u in get_all_users():
        if u["username"] == username:
            return u
    return None

SECRET_QUESTIONS = [
    "子供の頃のニックネームは？",
    "小学校の名前は？",
    "初めて飼ったペットの名前は？",
    "好きな食べ物は？",
    "母親の旧姓は？",
    "生まれた市区町村は？",
    "好きなアーティスト・バンド名は？",
]

def add_user(username, password, name, role, employee_type=None, hourly_wage=None,
             secret_question=None, secret_answer=None):
    data = load_json("users.json", {"users": []})
    for u in data["users"]:
        if u["username"] == username:
            return False
    emp_type = employee_type or ("seishain" if role == "admin" else "baito")
    wage = hourly_wage if hourly_wage is not None else (1500 if emp_type == "seishain" else 1050)
    data["users"].append({
        "username": username, "password": _hash(password),
        "name": name, "role": role,
        "employee_type": emp_type,
        "hourly_wage": wage,
        "birthday": "",
        "coco_spec": {"service": None, "cooking": None},
        "secret_question": secret_question or "",
        "secret_answer": _hash(secret_answer.strip().lower()) if secret_answer else "",
        "joined": datetime.now().strftime("%Y-%m-%d"),
    })
    save_json("users.json", data)
    return True

def verify_secret_answer(username, answer):
    """秘密の質問の答えを照合する。"""
    users = load_json("users.json", {"users": []}).get("users", [])
    for u in users:
        if u["username"] == username:
            stored = u.get("secret_answer", "")
            return stored and stored == _hash(answer.strip().lower())
    return False

def get_secret_question(username):
    """ユーザーの秘密の質問を返す。"""
    users = load_json("users.json", {"users": []}).get("users", [])
    for u in users:
        if u["username"] == username:
            return u.get("secret_question", "")
    return None  # ユーザーが存在しない場合

def reset_password(username, new_password):
    data = load_json("users.json", {"users": []})
    for u in data["users"]:
        if u["username"] == username:
            u["password"] = _hash(new_password)
    save_json("users.json", data)

def delete_user(username):
    data = load_json("users.json", {"users": []})
    data["users"] = [u for u in data["users"] if u["username"] != username]
    save_json("users.json", data)

def update_user(username, **kwargs):
    data = load_json("users.json", {"users": []})
    for u in data["users"]:
        if u["username"] == username:
            for field in ("role", "name", "employee_type", "hourly_wage",
                          "birthday", "coco_spec", "secret_question"):
                if field in kwargs:
                    u[field] = kwargs[field]
            if "password" in kwargs:
                u["password"] = _hash(kwargs["password"])
            if "secret_answer" in kwargs and kwargs["secret_answer"]:
                u["secret_answer"] = _hash(kwargs["secret_answer"].strip().lower())
    save_json("users.json", data)

# ─── 進捗管理 ─────────────────────────────────────────────────
def get_progress(username):
    data = load_json("progress.json", {})
    return data.get(username, {
        "stamps": [],
        "quiz_scores": [],
        "quiz_attempts": 0,
        "checklist_completions": {},
        "manual_read": [],
        "order_count": 0,
    })

def save_progress(username, progress):
    data = load_json("progress.json", {})
    data[username] = progress
    save_json("progress.json", data)

def award_stamps(username):
    p = get_progress(username)
    stamps = set(p.get("stamps", []))
    stamps.add("first_login")

    scores = p.get("quiz_scores", [])
    cl = p.get("checklist_completions", {})

    if scores and max(scores) >= 7:
        stamps.add("quiz_pass")
    if scores and max(scores) == 10:
        stamps.add("quiz_perfect")
    if len(p.get("manual_read", [])) >= 3:
        stamps.add("manual_reader")
    if cl.get("開店前チェック", 0) >= 3:
        stamps.add("opening_master")
    if cl.get("閉店作業チェック", 0) >= 3:
        stamps.add("closing_master")
    if cl.get("衛生管理チェック", 0) >= 5:
        stamps.add("hygiene_master")
    if cl.get("接客中チェック", 0) >= 5:
        stamps.add("service_pro")
    if p.get("order_count", 0) >= 10:
        stamps.add("order_master")
    if len(stamps) >= 8:
        stamps.add("all_star")

    old = set(p.get("stamps", []))
    p["stamps"] = list(stamps)
    save_progress(username, p)
    return p, stamps - old  # new stamps earned

# ─── Streamlit ヘルパー ───────────────────────────────────────
def apply_theme():
    st.markdown(THEME_CSS, unsafe_allow_html=True)

def require_login():
    if not st.session_state.get("user"):
        st.warning("⚠️ ログインが必要です。")
        st.stop()

def require_admin():
    """管理者（admin）専用。"""
    require_login()
    if st.session_state.user.get("role") != "admin":
        st.error("🚫 管理者権限が必要です。")
        st.stop()

def require_manager():
    """管理者または代行が使えるページ用。"""
    require_login()
    if not is_manager(st.session_state.user):
        st.error("🚫 管理者または代行の権限が必要です。")
        st.stop()

def sidebar_user():
    user = st.session_state.get("user", {})
    role_label = ROLE_LABELS.get(user.get("role", ""), "")
    store = get_store_settings()
    branch = store.get("store_branch", "")
    store_line = store.get("store_name", "CoCo壱番屋") + (f" {branch}" if branch else "")

    st.sidebar.markdown(f"""
<div class="sidebar-user">
  <div class="name">👤 {user.get('name', '')}</div>
  <div class="role">{role_label}</div>
  <div style="font-size:0.72rem;color:#888;margin-top:4px;">{store_line}</div>
</div>
""", unsafe_allow_html=True)
    st.sidebar.markdown("""
<style>
/* ログアウトボタン */
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #cccccc !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    font-size: 0.85rem !important;
    padding: 6px 12px !important;
    margin: 0 8px !important;
    width: calc(100% - 16px) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(220,53,69,0.2) !important;
    border-color: rgba(220,53,69,0.5) !important;
    color: #ff6b6b !important;
}
</style>
""", unsafe_allow_html=True)
    if st.sidebar.button("🚪 ログアウト", use_container_width=True):
        try:
            import extra_streamlit_components as stx
            cm = stx.CookieManager(key="logout_cm")
            cm.delete("coco_login")
        except Exception:
            pass
        st.session_state.user = None
        st.rerun()

def page_header(title, subtitle=""):
    sub = f"<p>{subtitle}</p>" if subtitle else ""
    st.markdown(f'<div class="page-header"><h1>{title}</h1>{sub}</div>', unsafe_allow_html=True)

def show_new_stamps(new_stamps):
    if new_stamps:
        for s in new_stamps:
            info = STAMPS.get(s, {})
            st.toast(f"{info.get('emoji','')} 新スタンプ獲得！「{info.get('name','')}」", icon="🎉")

# ─── シフト管理 ────────────────────────────────────────────────

def get_shift_deadline(year_month):
    """締切日を返す。デフォルトは前月10日。"""
    data = load_json("shift_requests.json", {})
    overrides = data.get("_deadlines", {})
    if year_month in overrides:
        return overrides[year_month]
    y, m = map(int, year_month.split("-"))
    if m == 1:
        prev_y, prev_m = y - 1, 12
    else:
        prev_y, prev_m = y, m - 1
    return f"{prev_y:04d}-{prev_m:02d}-10"

def set_shift_deadline(year_month, deadline_str):
    data = load_json("shift_requests.json", {})
    if "_deadlines" not in data:
        data["_deadlines"] = {}
    data["_deadlines"][year_month] = deadline_str
    save_json("shift_requests.json", data)

def submit_shift_request(username, year_month, entries):
    """entries: {date_str: {type:'work'|'off', start:str, end:str, note:str}}"""
    data = load_json("shift_requests.json", {})
    if year_month not in data:
        data[year_month] = {}
    data[year_month][username] = {
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "entries": entries,
    }
    save_json("shift_requests.json", data)

def get_user_shift_request(username, year_month):
    data = load_json("shift_requests.json", {})
    return data.get(year_month, {}).get(username)

def get_all_shift_requests(year_month):
    data = load_json("shift_requests.json", {})
    return {k: v for k, v in data.get(year_month, {}).items() if not k.startswith("_")}

def get_shift_schedule(date_str):
    data = load_json("shift_schedules.json", {})
    return data.get(date_str, {"sales_target": 0, "min_staff": 3, "shifts": {}})

def save_shift_schedule(date_str, schedule_data):
    data = load_json("shift_schedules.json", {})
    data[date_str] = schedule_data
    save_json("shift_schedules.json", data)

def get_employee_type(user):
    """employee_type フィールドがない場合は role から推定する。"""
    return user.get("employee_type", "seishain" if user.get("role") == "admin" else "baito")

# CoCoスペ
SERVICE_LEVELS = [None, "3級", "2級", "1級", "スター"]
COOKING_LEVELS = [None, "3級", "2級", "1級"]

def get_coco_spec(user):
    spec = user.get("coco_spec", {}) or {}
    return {"service": spec.get("service"), "cooking": spec.get("cooking")}

def coco_spec_badge(spec):
    """HTML バッジ文字列を返す。"""
    parts = []
    svc = spec.get("service")
    ckng = spec.get("cooking")
    if svc:
        color = "#e85d04" if svc == "スター" else "#5b4b97"
        parts.append(f"<span style='background:{color};color:#fff;padding:2px 8px;"
                     f"border-radius:10px;font-size:12px;'>接客 {svc}</span>")
    if ckng:
        parts.append(f"<span style='background:#1e6ab5;color:#fff;padding:2px 8px;"
                     f"border-radius:10px;font-size:12px;'>調理 {ckng}</span>")
    return " ".join(parts) if parts else "<span style='color:#999;font-size:12px;'>未設定</span>"

# ─── ファイル添付管理 ──────────────────────────────────────────
FILES_DIR = os.path.join(DATA_DIR, "files")

def _ensure_files_dir():
    os.makedirs(FILES_DIR, exist_ok=True)

def get_attachments(section_type, section_id):
    """section_type: 'manual' | 'checklist'"""
    data = load_json("file_attachments.json", {})
    return data.get(section_type, {}).get(str(section_id), [])

def save_uploaded_file(uploaded_file):
    """UploadedFile を保存し (filename, file_type) を返す。"""
    import uuid
    _ensure_files_dir()
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    filename = f"{uuid.uuid4().hex}{ext}"
    with open(os.path.join(FILES_DIR, filename), "wb") as f:
        f.write(uploaded_file.getbuffer())
    if ext in (".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"):
        ftype = "image"
    elif ext in (".mp4", ".avi", ".mov", ".webm", ".mkv"):
        ftype = "video"
    else:
        ftype = "file"
    return filename, ftype

def add_attachment(section_type, section_id, filename, original_name, file_type):
    data = load_json("file_attachments.json", {})
    data.setdefault(section_type, {}).setdefault(str(section_id), [])
    data[section_type][str(section_id)].append({
        "filename": filename,
        "original_name": original_name,
        "type": file_type,
        "uploaded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    })
    save_json("file_attachments.json", data)

def delete_attachment(section_type, section_id, filename):
    data = load_json("file_attachments.json", {})
    key = str(section_id)
    if section_type in data and key in data[section_type]:
        data[section_type][key] = [
            a for a in data[section_type][key] if a.get("filename") != filename
        ]
    save_json("file_attachments.json", data)
    fp = os.path.join(FILES_DIR, filename)
    if os.path.exists(fp):
        os.remove(fp)

def render_attachments(section_type, section_id, allow_delete=False):
    """添付ファイルを表示する。allow_delete=True なら削除ボタン付き。"""
    attachments = get_attachments(section_type, section_id)
    if not attachments:
        return
    st.markdown("**📎 添付ファイル**")
    for att in attachments:
        fp = os.path.join(FILES_DIR, att["filename"])
        if not os.path.exists(fp):
            continue
        col_media, col_del = st.columns([10, 1]) if allow_delete else (st, None)
        with col_media:
            if att["type"] == "image":
                st.image(fp, caption=att["original_name"], use_container_width=True)
            elif att["type"] == "video":
                st.video(fp)
            else:
                with open(fp, "rb") as f:
                    st.download_button(f"📄 {att['original_name']}", f.read(),
                                       file_name=att["original_name"],
                                       key=f"dl_{att['filename']}")
        if allow_delete and col_del:
            with col_del:
                if st.button("🗑️", key=f"delatc_{section_type}_{section_id}_{att['filename']}",
                             help="削除"):
                    delete_attachment(section_type, section_id, att["filename"])
                    st.rerun()

def upload_attachment_ui(section_type, section_id, label="ファイルをアップロード"):
    """管理者用のアップロードUI。"""
    uploaded = st.file_uploader(
        label,
        type=["jpg", "jpeg", "png", "gif", "webp", "mp4", "mov", "avi", "webm", "pdf", "txt"],
        key=f"uploader_{section_type}_{section_id}",
    )
    if uploaded:
        if st.button("📤 アップロード", key=f"upload_btn_{section_type}_{section_id}",
                     type="primary"):
            filename, ftype = save_uploaded_file(uploaded)
            add_attachment(section_type, section_id, filename, uploaded.name, ftype)
            st.success(f"✅ {uploaded.name} をアップロードしました。")
            st.rerun()


def get_today_birthdays(exclude_username=None):
    """今日が誕生日のユーザーリストを返す。"""
    from datetime import datetime
    today_mmdd = datetime.now().strftime("%m-%d")
    users = load_json("users.json", {"users": []}).get("users", [])
    result = []
    for u in users:
        bd = u.get("birthday", "")
        if bd and bd[-5:] == today_mmdd:
            if exclude_username and u["username"] == exclude_username:
                continue
            result.append(u)
    return result

# ─── 店舗設定 ──────────────────────────────────────────────────
def get_store_settings():
    return load_json("store_settings.json", {
        "store_name": "CoCo壱番屋",
        "store_branch": "",
    })

def save_store_settings(**kwargs):
    current = get_store_settings()
    current.update(kwargs)
    save_json("store_settings.json", current)
