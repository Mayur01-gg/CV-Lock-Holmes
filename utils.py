import json
import re
import tempfile
from datetime import datetime

import streamlit as st
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

        return re.sub(r'\s+', ' ', text).strip()
    except Exception as e:
        st.error(f"PDF extraction failed: {e}")
        return None


# -------------------- JSON EXTRACTION (CRITICAL FIX) --------------------

def extract_json_from_text(text):
    """
    Safely extracts the first valid JSON object from Gemini response
    """
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise ValueError("No JSON object found in response")
        return json.loads(match.group())
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON returned by Gemini") from e


# -------------------- GEMINI RESUME ANALYSIS --------------------

def analyze_resume_with_gemini(resume_text, job_description):
    try:
        api_key = st.session_state.get("api_key")
        if not api_key:
            st.error("Gemini API key not provided")
            return None

        client = genai.Client(api_key=api_key)

        prompt = f"""
You are an expert Technical Recruiter and ATS specialist.

STRICT RULES:
- Respond ONLY with valid JSON
- No markdown
- No explanations
- No text outside JSON

JSON FORMAT:
{{
  "match_score": 0-100,
  "missing_skills": [],
  "profile_summary": "",
  "improvements": []
}}

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )

        raw_text = response.text.strip()

        # DEBUG LOG (remove later if needed)
        print("GEMINI RAW RESPONSE:\n", raw_text)

        analysis = extract_json_from_text(raw_text)
        analysis["match_score"] = int(analysis.get("match_score", 0))

        return analysis

    except Exception as e:
        st.error(f"Gemini analysis failed: {e}")
        return None


# -------------------- GAUGE CHART --------------------

def create_gauge_chart(score):
    color = "green" if score >= 80 else "yellow" if score >= 60 else "red"

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": "Match Score"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 60], "color": "#ffcccc"},
                {"range": [60, 80], "color": "#ffffcc"},
                {"range": [80, 100], "color": "#ccffcc"},
            ],
        },
    ))

    fig.update_layout(height=300)
    return fig


# -------------------- EXPORT REPORT --------------------

def export_analysis(analysis, filename, job_title):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    report = f"""
AI RESUME ANALYSIS REPORT
------------------------
Generated: {ts}
File: {filename}
Job: {job_title}

MATCH SCORE: {analysis['match_score']}%

SUMMARY:
{analysis['profile_summary']}

MISSING SKILLS:
{', '.join(analysis['missing_skills']) or 'None'}

IMPROVEMENTS:
"""
    for i, imp in enumerate(analysis["improvements"], 1):
        report += f"\n{i}. {imp}"

    return report


# -------------------- API KEY VALIDATION --------------------

def validate_api_key(api_key):
    try:
        client = genai.Client(api_key=api_key)
        client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Hello"
        )
        return True
    except Exception:
        return False
