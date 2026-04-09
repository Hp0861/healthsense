"""
app.py – HealthSense Streamlit frontend.

Run with:
    streamlit run frontend/app.py
"""

import io
import sys
from pathlib import Path

import requests
import streamlit as st
from PIL import Image

# ── Make sure repo root is importable ────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

API = "http://localhost:8000/api/v1"

# ────────────────────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="HealthSense",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────────────────────────────────────────────────────
# CSS theming
# ────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <style>
    /* ---------- global ---------- */
    body { font-family: 'Segoe UI', sans-serif; }

    /* ---------- flag badges ---------- */
    .flag-high   { background:#fde8e8; color:#c0392b; padding:2px 10px;
                   border-radius:12px; font-weight:700; font-size:.85rem; }
    .flag-low    { background:#e8f0fe; color:#1a73e8; padding:2px 10px;
                   border-radius:12px; font-weight:700; font-size:.85rem; }
    .flag-normal { background:#e6f4ea; color:#137333; padding:2px 10px;
                   border-radius:12px; font-weight:700; font-size:.85rem; }

    /* ---------- cards ---------- */
    .result-card {
        border:1px solid #e0e0e0;
        border-radius:10px;
        padding:14px 18px;
        margin-bottom:12px;
        background:#fafafa;
    }
    .result-card h4 { margin:0 0 4px 0; font-size:1rem; color:#202124; }
    .result-value   { font-size:1.4rem; font-weight:700; color:#202124; }
    .result-range   { color:#5f6368; font-size:.85rem; }

    /* ---------- sidebar ---------- */
    section[data-testid="stSidebar"] { background:#f1f8ff; }

    /* ---------- disclaimer ---------- */
    .disclaimer {
        background:#fff8e1;
        border-left:4px solid #f9a825;
        padding:10px 14px;
        border-radius:4px;
        font-size:.85rem;
        color:#555;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ────────────────────────────────────────────────────────────────────────────
# Session-state helpers
# ────────────────────────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "logged_in": False,
        "user_id": None,
        "username": "",
        "page": "login",
        "active_profile": None,   # dict  {id, name, relation, age}
        "profiles": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()


def go_to(page: str):
    st.session_state.page = page
    st.rerun()


# ────────────────────────────────────────────────────────────────────────────
# API helpers
# ────────────────────────────────────────────────────────────────────────────

def api_post(path: str, json: dict) -> dict:
    try:
        r = requests.post(f"{API}{path}", json=json, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot reach the backend. Is `uvicorn backend.main:app` running on port 8000?")
        return {}
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"API error: {detail}")
        return {}


def api_get(path: str) -> dict | list:
    try:
        r = requests.get(f"{API}{path}", timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot reach the backend.")
        return {}
    except requests.exceptions.HTTPError as e:
        st.error(f"API error: {e}")
        return {}


def api_upload(path: str, files: dict, data: dict) -> dict:
    try:
        r = requests.post(f"{API}{path}", files=files, data=data, timeout=60)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot reach the backend.")
        return {}
    except requests.exceptions.HTTPError as e:
        detail = e.response.json().get("detail", str(e))
        st.error(f"Upload error: {detail}")
        return {}


def load_profiles():
    if st.session_state.user_id:
        data = api_get(f"/profiles/{st.session_state.user_id}")
        st.session_state.profiles = data if isinstance(data, list) else []


# ────────────────────────────────────────────────────────────────────────────
# Reusable widgets
# ────────────────────────────────────────────────────────────────────────────

def _flag_badge(flag: str) -> str:
    cls = f"flag-{flag.lower()}"
    icons = {"HIGH": "🔴", "LOW": "🔵", "NORMAL": "🟢"}
    icon = icons.get(flag, "⚪")
    return f'<span class="{cls}">{icon} {flag}</span>'


def render_test_card(test: dict, expanded: bool = False):
    flag = test.get("flag", "NORMAL")
    badge = _flag_badge(flag)
    name  = test.get("test_name", "—")
    value = test.get("value", "—")
    unit  = test.get("unit", "")
    rng   = test.get("range_text") or "—"
    expl  = test.get("explanation", "")

    card_color = {
        "HIGH":   "#fff5f5",
        "LOW":    "#f0f4ff",
        "NORMAL": "#f6fef6",
    }.get(flag, "#fafafa")

    st.markdown(
        f"""
        <div class="result-card" style="background:{card_color}">
            <h4>{name} &nbsp; {badge}</h4>
            <span class="result-value">{value} {unit}</span>
            <span class="result-range">&nbsp;|&nbsp; Ref: {rng}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if expl:
        with st.expander("ℹ️ What does this mean?", expanded=expanded):
            st.markdown(expl)


# ────────────────────────────────────────────────────────────────────────────
# Sidebar navigation
# ────────────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.image(
            "https://img.icons8.com/color/96/hospital.png",
            width=64,
        )
        st.title("HealthSense 🏥")
        st.caption("Family Health Report App")
        st.divider()

        if not st.session_state.logged_in:
            st.info("Please log in to continue.")
            return

        st.success(f"👤 {st.session_state.username}")

        # Profile selector
        st.subheader("Active Profile")
        profiles = st.session_state.profiles
        if profiles:
            names = [f"{p['name']} ({p['relation']})" for p in profiles]
            idx = 0
            if st.session_state.active_profile:
                try:
                    idx = next(
                        i for i, p in enumerate(profiles)
                        if p["id"] == st.session_state.active_profile["id"]
                    )
                except StopIteration:
                    idx = 0
            chosen = st.selectbox("Select profile", names, index=idx, key="sb_profile")
            st.session_state.active_profile = profiles[names.index(chosen)]
        else:
            st.caption("No profiles yet.")

        st.divider()
        st.subheader("Navigation")
        pages = {
            "🏠 Dashboard":      "dashboard",
            "⬆️ Upload Report":  "upload",
            "📋 Report History": "history",
            "👥 Manage Profiles":"profiles",
        }
        for label, pg in pages.items():
            if st.button(label, use_container_width=True):
                go_to(pg)

        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            for k in ["logged_in", "user_id", "username", "active_profile", "profiles"]:
                st.session_state[k] = False if k == "logged_in" else None if "id" in k or k == "active_profile" else [] if k == "profiles" else ""
            go_to("login")


# ────────────────────────────────────────────────────────────────────────────
# Pages
# ────────────────────────────────────────────────────────────────────────────

# ── Login page ───────────────────────────────────────────────────────────────

def page_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://img.icons8.com/color/96/hospital.png", width=80)
        st.title("HealthSense")
        st.subheader("Your Family Health Companion")
        st.caption("India-focused • Safe • Informational")
        st.divider()

        tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

        with tab_login:
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    if not username or not password:
                        st.warning("Please fill in all fields.")
                    else:
                        data = api_post("/auth/login", {"username": username, "password": password})
                        if data.get("success"):
                            st.session_state.logged_in = True
                            st.session_state.user_id   = data["user_id"]
                            st.session_state.username  = data["username"]
                            load_profiles()
                            go_to("dashboard")

        with tab_register:
            with st.form("register_form"):
                new_user = st.text_input("Choose a username")
                new_pass = st.text_input("Choose a password", type="password")
                submitted = st.form_submit_button("Register", use_container_width=True)
                if submitted:
                    if not new_user or not new_pass:
                        st.warning("Please fill in all fields.")
                    elif len(new_pass) < 4:
                        st.warning("Password must be at least 4 characters.")
                    else:
                        data = api_post("/auth/register", {"username": new_user, "password": new_pass})
                        if data.get("success"):
                            st.success("✅ Registered! Please log in.")

        st.markdown(
            '<div class="disclaimer">⚕️ HealthSense is for informational purposes only. '
            "All reports should be reviewed by a qualified doctor.</div>",
            unsafe_allow_html=True,
        )


# ── Dashboard page ────────────────────────────────────────────────────────────

def page_dashboard():
    profile = st.session_state.active_profile

    st.title("🏠 Dashboard")
    st.markdown(
        '<div class="disclaimer">⚕️ All information shown is for educational purposes only. '
        "Please consult a doctor for medical advice.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    if not profile:
        st.info("👈 Please select or create a profile from the sidebar to get started.")
        if st.button("➕ Add First Profile"):
            go_to("profiles")
        return

    st.subheader(f"📊 {profile['name']} ({profile['relation']})")
    if profile.get("age"):
        st.caption(f"Age: {profile['age']} years")

    # Load reports
    reports = api_get(f"/reports/profile/{profile['id']}")
    if not reports:
        st.info("No reports uploaded yet for this profile.")
        if st.button("⬆️ Upload First Report"):
            go_to("upload")
        return

    # Summary metrics from latest report
    latest = reports[0]
    tests  = latest.get("test_results", [])

    n_high   = sum(1 for t in tests if t["flag"] == "HIGH")
    n_low    = sum(1 for t in tests if t["flag"] == "LOW")
    n_normal = sum(1 for t in tests if t["flag"] == "NORMAL")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Reports", len(reports))
    c2.metric("🔴 High",   n_high)
    c3.metric("🔵 Low",    n_low)
    c4.metric("🟢 Normal", n_normal)

    st.divider()
    st.subheader(f"Latest Report  •  {latest.get('report_date') or latest['created_at'][:10]}")

    if not tests:
        st.warning("No test results were extracted from the latest report.")
        return

    # Flags summary
    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.markdown("#### Test Results")
        for t in tests:
            render_test_card(t)

    with col_b:
        st.markdown("#### Flags Summary")
        if n_high:
            st.error(f"🔴 {n_high} value(s) above normal range")
        if n_low:
            st.warning(f"🔵 {n_low} value(s) below normal range")
        if n_normal:
            st.success(f"🟢 {n_normal} value(s) within normal range")

        st.markdown(
            '<div class="disclaimer" style="margin-top:12px">'
            "Values outside the reference range do not necessarily indicate disease. "
            "Please consult a qualified doctor for interpretation.</div>",
            unsafe_allow_html=True,
        )


# ── Upload page ───────────────────────────────────────────────────────────────

def page_upload():
    st.title("⬆️ Upload Health Report")
    st.markdown(
        '<div class="disclaimer">⚕️ Uploaded images are processed locally. '
        "We do not share your data with any third party.</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

    profiles = st.session_state.profiles
    if not profiles:
        st.warning("Please create a profile first.")
        if st.button("➕ Create Profile"):
            go_to("profiles")
        return

    with st.form("upload_form"):
        profile_labels = [f"{p['name']} ({p['relation']})" for p in profiles]
        selected_label = st.selectbox("Select profile", profile_labels)
        selected_profile = profiles[profile_labels.index(selected_label)]

        report_date = st.date_input("Report date (optional)", value=None)
        uploaded_file = st.file_uploader(
            "Upload report image (PNG, JPG, JPEG, TIFF)",
            type=["png", "jpg", "jpeg", "tiff", "tif"],
        )

        submitted = st.form_submit_button("🔍 Process Report", use_container_width=True)

    if submitted:
        if not uploaded_file:
            st.warning("Please upload an image first.")
            return

        with st.spinner("🔍 Running OCR and extracting test results…"):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            data  = {
                "profile_id":  str(selected_profile["id"]),
                "report_date": str(report_date) if report_date else "",
            }
            result = api_upload("/reports/upload", files=files, data=data)

        if not result.get("success"):
            st.error("Upload failed. Please try again.")
            return

        st.success(f"✅ Report processed! {result['tests_found']} test(s) extracted.")

        # Show image preview
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Uploaded Image")
            img = Image.open(io.BytesIO(uploaded_file.getvalue()))
            st.image(img, use_container_width=True)

        with col2:
            st.subheader("Extracted Test Results")
            results = result.get("results", [])
            if results:
                for t in results:
                    render_test_card(t)
            else:
                st.info("No structured test data could be extracted. "
                        "The OCR text preview is shown below.")
                st.text(result.get("raw_text_preview", ""))

        # Update profile and navigate
        st.session_state.active_profile = selected_profile
        load_profiles()


# ── Report History page ───────────────────────────────────────────────────────

def page_history():
    profile = st.session_state.active_profile

    st.title("📋 Report History")

    if not profile:
        st.info("Please select a profile from the sidebar.")
        return

    st.subheader(f"Reports for: {profile['name']} ({profile['relation']})")

    reports = api_get(f"/reports/profile/{profile['id']}")
    if not reports:
        st.info("No reports found for this profile.")
        if st.button("⬆️ Upload a Report"):
            go_to("upload")
        return

    for idx, rpt in enumerate(reports):
        date_label = rpt.get("report_date") or rpt["created_at"][:10]
        tests      = rpt.get("test_results", [])
        n_high     = sum(1 for t in tests if t["flag"] == "HIGH")
        n_low      = sum(1 for t in tests if t["flag"] == "LOW")

        summary_badges = ""
        if n_high:
            summary_badges += f' <span class="flag-high">🔴 {n_high} HIGH</span>'
        if n_low:
            summary_badges += f' <span class="flag-low">🔵 {n_low} LOW</span>'
        if not n_high and not n_low:
            summary_badges = ' <span class="flag-normal">🟢 All Normal</span>'

        with st.expander(
            f"📄 Report #{idx + 1}  —  {date_label}  •  {len(tests)} test(s)",
            expanded=(idx == 0),
        ):
            st.markdown(
                f"**Date:** {date_label} &nbsp;|&nbsp; "
                f"**Tests:** {len(tests)} &nbsp;|&nbsp; {summary_badges}",
                unsafe_allow_html=True,
            )
            st.divider()

            if tests:
                for t in tests:
                    render_test_card(t)
            else:
                st.caption("No test results were extracted for this report.")


# ── Profiles management page ──────────────────────────────────────────────────

def page_profiles():
    st.title("👥 Manage Family Profiles")

    RELATIONS = ["Self", "Father", "Mother", "Child", "Spouse", "Other"]

    with st.expander("➕ Add New Profile", expanded=True):
        with st.form("add_profile_form"):
            col1, col2, col3 = st.columns(3)
            name     = col1.text_input("Name *")
            relation = col2.selectbox("Relation", RELATIONS)
            age      = col3.number_input("Age (optional)", min_value=0, max_value=120, value=0)

            submitted = st.form_submit_button("Add Profile", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.warning("Name is required.")
                else:
                    data = api_post(
                        "/profiles",
                        {
                            "user_id":  st.session_state.user_id,
                            "name":     name.strip(),
                            "relation": relation,
                            "age":      int(age) if age > 0 else None,
                        },
                    )
                    if data.get("id"):
                        st.success(f"✅ Profile '{name}' added!")
                        load_profiles()
                        st.rerun()

    st.divider()
    st.subheader("Your Profiles")
    load_profiles()
    profiles = st.session_state.profiles

    if not profiles:
        st.info("No profiles yet. Add your first profile above.")
        return

    for p in profiles:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 2, 1])
        col1.markdown(f"**{p['name']}**")
        col2.caption(p["relation"])
        col3.caption(f"Age: {p['age'] or '—'}")
        if col4.button("Set Active", key=f"active_{p['id']}"):
            st.session_state.active_profile = p
            st.success(f"Active profile set to {p['name']}")
            st.rerun()
        if col5.button("🗑️", key=f"del_{p['id']}", help="Delete profile"):
            requests.delete(f"{API}/profiles/{p['id']}")
            load_profiles()
            if st.session_state.active_profile and st.session_state.active_profile["id"] == p["id"]:
                st.session_state.active_profile = None
            st.rerun()


# ────────────────────────────────────────────────────────────────────────────
# Router
# ────────────────────────────────────────────────────────────────────────────

render_sidebar()

if not st.session_state.logged_in:
    page_login()
else:
    page = st.session_state.page
    if page == "dashboard":
        page_dashboard()
    elif page == "upload":
        page_upload()
    elif page == "history":
        page_history()
    elif page == "profiles":
        page_profiles()
    else:
        page_dashboard()
