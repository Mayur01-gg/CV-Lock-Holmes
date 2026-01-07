import json
import re
import tempfile
from datetime import datetime

from google import genai
import plotly.graph_objects as go

# PDF extraction libraries
try:
    from pdfminer.high_level import extract_text as pdfminer_extract
    PDF_LIBRARY = "pdfminer"
except ImportError:
    from PyPDF2 import PdfReader
    PDF_LIBRARY = "pypdf2"


# -------------------- PDF TEXT EXTRACTION --------------------

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file."""
    try:
        if PDF_LIBRARY == "pdfminer":
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(pdf_file.read())
                tmp_path = tmp.name
            text = pdfminer_extract(tmp_path)
        else:
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text

        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None


# -------------------- GEMINI RESUME ANALYSIS --------------------

def analyze_resume_with_gemini(resume_text, job_description, api_key):
    """Analyze resume using Gemini AI and return structured results."""
    try:
        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert Technical Recruiter and ATS (Applicant Tracking System) specialist.
Analyze the following resume against the job description and provide a detailed assessment.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Respond ONLY with valid JSON in this exact format:
{{
    "match_score": 0-100,
    "missing_skills": ["skill1", "skill2"],
    "profile_summary": "3 sentence summary",
    "improvements": ["improvement1", "improvement2"]
}}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        response_text = response.text.strip()

        # Extract JSON safely
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON found in Gemini response")

        analysis = json.loads(match.group())

        # Validate fields
        required_fields = ["match_score", "missing_skills", "profile_summary", "improvements"]
        if not all(field in analysis for field in required_fields):
            raise ValueError("Missing required fields in Gemini response")

        analysis["match_score"] = int(analysis["match_score"])

        return analysis

    except Exception as e:
        print(f"Gemini analysis error: {e}")
        return None


# -------------------- GAUGE CHART --------------------

def create_gauge_chart(score):
    """Create a gauge chart for the match score."""
    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellow"
    else:
        color = "red"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Match Score", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 60], 'color': '#ffcccc'},
                {'range': [60, 80], 'color': '#ffffcc'},
                {'range': [80, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': 'red', 'width': 4},
                'value': 90
            }
        }
    ))

    fig.update_layout(height=300)
    return fig


# -------------------- EXPORT REPORT --------------------

def export_analysis(analysis_result, filename, job_title):
    """Export analysis results as formatted text."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
================ AI RESUME ANALYSIS REPORT ================

Generated: {timestamp}
Resume File: {filename}
Target Job: {job_title}

-----------------------------------------------------------

MATCH SCORE: {analysis_result['match_score']}%

PROFILE SUMMARY:
{analysis_result['profile_summary']}

-----------------------------------------------------------

MISSING SKILLS:
"""

    if analysis_result["missing_skills"]:
        for i, skill in enumerate(analysis_result["missing_skills"], 1):
            report += f"\n{i}. {skill}"
    else:
        report += "\nAll required skills present."

    report += "\n\nIMPROVEMENTS:\n"

    for i, improvement in enumerate(analysis_result["improvements"], 1):
        report += f"\n{i}. {improvement}"

    report += "\n\n===========================================================\n"
    return report


# -------------------- API KEY VALIDATION --------------------

def validate_api_key(api_key):
    """Validate Gemini API key."""
    try:
        client = genai.Client(api_key=api_key)
        client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello"
        )
        return True
    except Exception as e:
        print(f"API key validation error: {e}")
        return False
