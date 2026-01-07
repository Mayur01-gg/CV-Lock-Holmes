import streamlit as st
import os
from datetime import datetime
from database import init_db, create_user, verify_user, save_analysis, get_user_history
from utils import extract_text_from_pdf, analyze_resume_with_gemini, create_gauge_chart, export_analysis
from google import genai

# Page configuration
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

# Sidebar for API Key
with st.sidebar:
    st.title("⚙️ Configuration")
    api_key = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API key")
    
    if api_key:
        genai.configure(api_key=api_key)
        st.success("✅ API Key configured")
    
    if st.session_state.logged_in:
        st.divider()
        st.write(f"👤 **User:** {st.session_state.username}")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.user_id = None
            st.session_state.page = 'dashboard'
            st.rerun()

def login_page():
    st.title("🔐 AI Resume Analyzer")
    st.subheader("Login to Your Account")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                user_id = verify_user(username, password)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_id = user_id
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            register = st.form_submit_button("Register", use_container_width=True)
            
            if register:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters")
                elif not new_username or not new_email:
                    st.error("All fields are required")
                else:
                    if create_user(new_username, new_email, new_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists")

def dashboard_page():
    st.title(f"👋 Welcome, {st.session_state.username}!")
    st.subheader("Your Resume Analysis Dashboard")
    
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🚀 Start New Analysis", use_container_width=True, type="primary"):
            st.session_state.page = 'upload'
            st.rerun()
    
    st.divider()
    
    # Fetch user history
    history = get_user_history(st.session_state.user_id)
    
    if history:
        st.subheader("📊 Analysis History")
        
        # Display metrics
        total_analyses = len(history)
        avg_score = sum([h[3] for h in history]) / total_analyses if total_analyses > 0 else 0
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total Analyses", total_analyses)
        with metric_col2:
            st.metric("Average Score", f"{avg_score:.1f}%")
        with metric_col3:
            latest_score = history[0][3] if history else 0
            st.metric("Latest Score", f"{latest_score}%")
        
        st.divider()
        
        # Display history table
        st.dataframe(
            {
                "Date": [h[1] for h in history],
                "Filename": [h[2] for h in history],
                "Match Score": [f"{h[3]}%" for h in history],
                "Job Title": [h[4] for h in history]
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No analysis history yet. Start your first analysis!")

def upload_page():
    st.title("📤 Upload Resume & Job Description")
    
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Upload Resume (PDF)")
        uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
    
    with col2:
        st.subheader("2. Job Description")
        job_description = st.text_area(
            "Paste the job description here",
            height=200,
            placeholder="Paste the complete job description including required skills, qualifications, and responsibilities..."
        )
        
        job_title = st.text_input("Job Title (Optional)", placeholder="e.g., Senior Software Engineer")
    
    st.divider()
    
    if st.button("🔍 Analyze Resume", type="primary", use_container_width=True):
        if not uploaded_file:
            st.error("Please upload a resume PDF")
        elif not job_description:
            st.error("Please provide a job description")
        elif not api_key:
            st.error("Please configure your Gemini API key in the sidebar")
        else:
            with st.spinner("Extracting text from PDF..."):
                resume_text = extract_text_from_pdf(uploaded_file)
            
            if not resume_text:
                st.error("Could not extract text from PDF. Please ensure it's a valid PDF file.")
                return
            
            with st.spinner("Analyzing resume with AI... This may take a moment."):
                analysis_result = analyze_resume_with_gemini(resume_text, job_description)
            
            if analysis_result:
                # Save to session state
                st.session_state.analysis_result = analysis_result
                st.session_state.uploaded_filename = uploaded_file.name
                st.session_state.job_title = job_title or "Not Specified"
                
                # Save to database
                save_analysis(
                    st.session_state.user_id,
                    uploaded_file.name,
                    analysis_result['match_score'],
                    job_title or "Not Specified",
                    str(analysis_result)
                )
                
                # Navigate to results
                st.session_state.page = 'results'
                st.rerun()
            else:
                st.error("Analysis failed. Please check your API key and try again.")

def results_page():
    st.title("📊 Analysis Results")
    
    if st.button("← Back to Dashboard"):
        st.session_state.page = 'dashboard'
        st.rerun()
    
    if 'analysis_result' not in st.session_state:
        st.warning("No analysis results found. Please upload a resume first.")
        return
    
    result = st.session_state.analysis_result
    
    st.divider()
    
    # Display match score with gauge chart
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Match Score")
        score = result['match_score']
        
        # Color-coded metric
        if score >= 80:
            score_color = "🟢"
            score_label = "Excellent Match"
        elif score >= 60:
            score_color = "🟡"
            score_label = "Good Match"
        else:
            score_color = "🔴"
            score_label = "Needs Improvement"
        
        st.markdown(f"### {score_color} {score}%")
        st.caption(score_label)
        
        # Create and display gauge chart
        gauge_fig = create_gauge_chart(score)
        st.plotly_chart(gauge_fig, use_container_width=True)
    
    with col2:
        st.subheader("Profile Summary")
        st.info(result['profile_summary'])
    
    st.divider()
    
    # Tabbed interface for detailed analysis
    tab1, tab2, tab3 = st.tabs(["🎯 Missing Skills", "💡 Improvements", "📝 Full Analysis"])
    
    with tab1:
        st.subheader("Skills to Add")
        if result['missing_skills']:
            for i, skill in enumerate(result['missing_skills'], 1):
                st.markdown(f"{i}. **{skill}**")
        else:
            st.success("Great! Your resume covers all key skills from the job description.")
    
    with tab2:
        st.subheader("Actionable Recommendations")
        if result['improvements']:
            for i, improvement in enumerate(result['improvements'], 1):
                st.markdown(f"{i}. {improvement}")
        else:
            st.success("Your resume is well-optimized!")
    
    with tab3:
        st.subheader("Complete Analysis Report")
        st.json(result)
    
    st.divider()
    
    # Export options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download Report (TXT)", use_container_width=True):
            report_text = export_analysis(result, st.session_state.uploaded_filename, st.session_state.job_title)
            st.download_button(
                "Download TXT",
                report_text,
                file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    with col2:
        if st.button("🔄 Analyze Another Resume", use_container_width=True):
            st.session_state.page = 'upload'
            st.rerun()

# Main app logic
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        # Navigation
        if st.session_state.page == 'dashboard':
            dashboard_page()
        elif st.session_state.page == 'upload':
            upload_page()
        elif st.session_state.page == 'results':
            results_page()

if __name__ == "__main__":
    main()