import json
import re
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

def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file."""
    try:
        if PDF_LIBRARY == "pdfminer":
            # Using pdfminer.six
            text = pdfminer_extract(pdf_file)
        else:
            # Using PyPDF2
            pdf_reader = PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
        
        # Clean up the text
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def analyze_resume_with_gemini(resume_text, job_description):
    """Analyze resume using Gemini AI and return structured results."""
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = f"""You are an expert Technical Recruiter and ATS (Applicant Tracking System) specialist. 
Analyze the following resume against the job description and provide a detailed assessment.

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Provide your analysis in the following JSON format (respond ONLY with valid JSON, no markdown):
{{
    "match_score": <integer 0-100>,
    "missing_skills": [<list of skills/keywords from JD not found in resume>],
    "profile_summary": "<3-sentence summary of candidate's strengths and fit>",
    "improvements": [<list of 5-7 actionable improvements to make the resume better>]
}}

Important:
- Be thorough in identifying missing skills by comparing JD keywords with resume
- Give realistic match scores based on actual overlap
- Provide specific, actionable improvements
- Focus on both technical skills and soft skills
- Consider ATS optimization in your suggestions"""

        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Parse JSON response
        analysis = json.loads(response_text)
        
        # Validate required fields
        required_fields = ['match_score', 'missing_skills', 'profile_summary', 'improvements']
        if not all(field in analysis for field in required_fields):
            raise ValueError("Missing required fields in API response")
        
        # Ensure match_score is an integer
        analysis['match_score'] = int(analysis['match_score'])
        
        return analysis
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response_text}")
        return None
    except Exception as e:
        print(f"Error in Gemini analysis: {e}")
        return None

def create_gauge_chart(score):
    """Create a gauge chart for the match score."""
    # Determine color based on score
    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellow"
    else:
        color = "red"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Match Score", 'font': {'size': 24}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 60], 'color': '#ffcccc'},
                {'range': [60, 80], 'color': '#ffffcc'},
                {'range': [80, 100], 'color': '#ccffcc'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor="white",
        font={'color': "darkblue", 'family': "Arial"}
    )
    
    return fig

def export_analysis(analysis_result, filename, job_title):
    """Export analysis results as formatted text."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
╔══════════════════════════════════════════════════════════════╗
║          AI RESUME ANALYSIS REPORT                           ║
╚══════════════════════════════════════════════════════════════╝

Report Generated: {timestamp}
Resume File: {filename}
Target Job: {job_title}

═══════════════════════════════════════════════════════════════

MATCH SCORE: {analysis_result['match_score']}%

═══════════════════════════════════════════════════════════════

PROFILE SUMMARY:
{analysis_result['profile_summary']}

═══════════════════════════════════════════════════════════════

MISSING SKILLS & KEYWORDS:
"""
    
    if analysis_result['missing_skills']:
        for i, skill in enumerate(analysis_result['missing_skills'], 1):
            report += f"\n  {i}. {skill}"
    else:
        report += "\n  ✓ All key skills from job description are present"
    
    report += "\n\n═══════════════════════════════════════════════════════════════\n\n"
    report += "RECOMMENDED IMPROVEMENTS:\n"
    
    if analysis_result['improvements']:
        for i, improvement in enumerate(analysis_result['improvements'], 1):
            report += f"\n  {i}. {improvement}\n"
    else:
        report += "\n  ✓ Resume is well-optimized"
    
    report += "\n═══════════════════════════════════════════════════════════════\n"
    report += "\nGenerated by AI Resume Analyzer\n"
    report += "═══════════════════════════════════════════════════════════════\n"
    
    return report

def validate_api_key(api_key):
    """Validate if the Gemini API key is working."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content("Test")
        return True
    except Exception as e:
        print(f"API key validation error: {e}")
        return False