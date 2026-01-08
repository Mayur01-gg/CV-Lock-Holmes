import streamlit as st
from datetime import datetime
from database import init_db, create_user, verify_user, save_analysis, get_user_history
from utils import extract_text_from_pdf, analyze_resume_with_gemini, create_gauge_chart, export_analysis

# -------------------- PAGE CONFIG --------------------

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- GLOBAL STYLES --------------------

st.markdown("""
<style>
/* Main background */
.main {
    background-color: #0e1117;
}

/* Section cards */
.card {
    background: #161b22;
    padding: 20px;
    border-radius: 14px;
    margin-bottom: 20px;
    border: 1px solid #30363d;
}

/* Headings */
h1, h2, h3 {
    color: #e6edf3;
}

/* Metric styling */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    padding: 15px;
    border-radius: 14px;
}

/* Buttons */
.stButton button {
    border-radius: 10px;
    height: 45px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #010409;
}
</style>
""", unsafe_allow_html=True)

# -------------------- INIT DB --------------------

init_db()

# -------------------- SESSION STATE --------------------

defaults = {
    "logged_in": False,
    "username": None,
    "user_id": None,
    "page": "dashboard",
    "api_key": None
}

for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# -------------------- SIDEBAR --------------------

with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key"
    )

    if api_key:
        st.session_state.api_key = api_key
        st.success("API key saved")

    if st.session_state.logged_in:
        st.divider()
        st.markdown(f"👤 **{st.session_state.username}**")

        if st.button("🚪 Logout", use_container_width=True):
            for key in ["logged_in", "username", "user_id", "page"]:
                st.session_state[key] = defaults[key]
            st.rerun()

# -------------------- AUTH --------------------

def login_page():
    st.markdown("<h1 style='text-align:center;'>AI Resume Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#9da7b1;'>Smart resume screening powered by AI</p>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    with tab1:
        with st.form("login"):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if submit:
                user_id = verify_user(u, p)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.user_id = user_id
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("register"):
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            u = st.text_input("Username")
            e = st.text_input("Email")
            p1 = st.text_input("Password", type="password")
            p2 = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

            if submit:
                if p1 != p2:
                    st.error("Passwords do not match")
                elif len(p1) < 6:
                    st.error("Password too short")
                elif create_user(u, e, p1):
                    st.success("Account created. Please login.")
                else:
                    st.error("Username already exists")

# -------------------- DASHBOARD --------------------

def dashboard_page():
    st.markdown(f"## 👋 Welcome, {st.session_state.username}")

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    if st.button("🚀 Start New Analysis", type="primary", use_container_width=True):
        st.session_state.page = "upload"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    history = get_user_history(st.session_state.user_id)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📊 Analysis History")

    if history:
        st.dataframe({
            "Date": [h[1] for h in history],
            "Resume": [h[2] for h in history],
            "Match Score": [f"{h[3]}%" for h in history],
            "Job Title": [h[4] for h in history],
        }, use_container_width=True)
    else:
        st.info("No analyses yet")
    st.markdown("</div>", unsafe_allow_html=True)

# -------------------- UPLOAD --------------------

def upload_page():
    st.markdown("## 📤 Upload Resume")

    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    resume = st.file_uploader("Resume (PDF)", type=["pdf"])
    jd = st.text_area("Job Description", height=200)
    job_title = st.text_input("Job Title (optional)")
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔍 Analyze Resume", type="primary", use_container_width=True):
        if not resume or not jd:
            st.error("Resume and Job Description required")
            return
        if not st.session_state.api_key:
            st.error("Please enter Gemini API key")
            return

        with st.spinner("Extracting resume..."):
            resume_text = extract_text_from_pdf(resume)

        with st.spinner("Analyzing with AI..."):
            result = analyze_resume_with_gemini(resume_text, jd)

        if result:
            st.session_state.analysis_result = result
            st.session_state.uploaded_filename = resume.name
            st.session_state.job_title = job_title or "Not Specified"

            save_analysis(
                st.session_state.user_id,
                resume.name,
                result["match_score"],
                st.session_state.job_title,
                str(result)
            )

            st.session_state.page = "results"
            st.rerun()

# -------------------- RESULTS --------------------

def results_page():
    result = st.session_state.analysis_result
    score = result["match_score"]

    st.markdown("## 📊 Resume Match Results")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("Match Score", f"{score}%")

    with col2:
        st.plotly_chart(create_gauge_chart(score), use_container_width=True)

    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("🧠 Profile Summary")
    st.write(result["profile_summary"])
    st.markdown("</div>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("❌ Missing Skills")
        for s in result["missing_skills"]:
            st.write(f"- {s}")
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("🚀 Improvement Suggestions")
        for i in result["improvements"]:
            st.write(f"- {i}")
        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("📥 Download Report", use_container_width=True):
        txt = export_analysis(
            result,
            st.session_state.uploaded_filename,
            st.session_state.job_title
        )
        st.download_button("Download Analysis", txt, file_name="resume_analysis.txt")

# -------------------- MAIN --------------------

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        {
            "dashboard": dashboard_page,
            "upload": upload_page,
            "results": results_page
        }[st.session_state.page]()

if __name__ == "__main__":
    main()
