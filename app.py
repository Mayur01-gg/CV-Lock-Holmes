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
    st.title("⚙️ Configuration")

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key"
    )

    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ API Key saved")

    if st.session_state.logged_in:
        st.divider()
        st.write(f"👤 **User:** {st.session_state.username}")

        if st.button("🚪 Logout", use_container_width=True):
            for key in ["logged_in", "username", "user_id", "page"]:
                st.session_state[key] = defaults[key]
            st.rerun()

# -------------------- AUTH PAGES --------------------

def login_page():
    st.title("🔐 AI Resume Analyzer")

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

            if submit:
                user_id = verify_user(u, p)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.user_id = user_id
                    st.success("Login successful")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    with tab2:
        with st.form("register"):
            u = st.text_input("Username")
            e = st.text_input("Email")
            p1 = st.text_input("Password", type="password")
            p2 = st.text_input("Confirm Password", type="password")
            submit = st.form_submit_button("Register", use_container_width=True)

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
    st.title(f"👋 Welcome, {st.session_state.username}")

    if st.button("🚀 Start New Analysis", type="primary"):
        st.session_state.page = "upload"
        st.rerun()

    history = get_user_history(st.session_state.user_id)

    if history:
        st.subheader("📊 Analysis History")
        st.dataframe({
            "Date": [h[1] for h in history],
            "File": [h[2] for h in history],
            "Score": [f"{h[3]}%" for h in history],
            "Job": [h[4] for h in history],
        }, use_container_width=True)
    else:
        st.info("No analyses yet")

# -------------------- UPLOAD PAGE --------------------

def upload_page():
    st.title("📤 Upload Resume")

    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()

    resume = st.file_uploader("Resume PDF", type=["pdf"])
    jd = st.text_area("Job Description", height=200)
    job_title = st.text_input("Job Title (optional)")

    if st.button("🔍 Analyze", type="primary"):
        if not resume or not jd:
            st.error("Resume and Job Description required")
            return
        if not st.session_state.api_key:
            st.error("Please enter Gemini API key in sidebar")
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
    st.title("📊 Results")

    result = st.session_state.analysis_result
    score = result["match_score"]

    st.metric("Match Score", f"{score}%")
    st.plotly_chart(create_gauge_chart(score), use_container_width=True)

    st.subheader("Profile Summary")
    st.info(result["profile_summary"])

    st.subheader("Missing Skills")
    for s in result["missing_skills"]:
        st.write(f"- {s}")

    st.subheader("Improvements")
    for i in result["improvements"]:
        st.write(f"- {i}")

    if st.button("📥 Download Report"):
        txt = export_analysis(result, st.session_state.uploaded_filename, st.session_state.job_title)
        st.download_button("Download", txt, file_name="analysis.txt")

# -------------------- MAIN --------------------

def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        {"dashboard": dashboard_page,
         "upload": upload_page,
         "results": results_page}[st.session_state.page]()

if __name__ == "__main__":
    main()
