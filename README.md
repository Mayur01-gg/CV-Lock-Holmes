# 🕵️ CV Lock Holmes

**CV Lock Holmes** is an AI-powered resume analysis and ATS scoring system that intelligently evaluates CVs using Generative AI.

## ✨ Features

- **🔐 Authentication System**: Secure login/register with hashed passwords using SQLite
- **📊 Dashboard**: View analysis history, statistics, and previous scores
- **📤 Resume Upload**: Support for PDF resume files with automatic text extraction
- **🤖 AI Analysis**: Powered by Google Gemini 1.5 Flash for intelligent resume evaluation
- **📈 Visual Results**: Interactive gauge charts and organized analysis tabs
- **💾 Export Function**: Download analysis reports in text format
- **🎨 Modern UI**: Clean, professional interface with responsive design

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key ([Get it here](https://makersuite.google.com/app/apikey))

### Installation

1. **Clone or download the project files**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (Optional):
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

4. **Run the application**:
```bash
streamlit run app.py
```

5. **Access the app**:
Open your browser and navigate to `http://localhost:8501`

## 📁 Project Structure

```
resume-analyzer/
│
├── app.py                 # Main Streamlit application
├── database.py            # Database operations and user management
├── utils.py               # Utility functions (PDF parsing, AI analysis)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
└── resume_analyzer.db    # SQLite database (created automatically)
```

## 🔧 Configuration

### API Key Setup

You can configure your Gemini API key in two ways:

1. **Via Sidebar** (Recommended for quick testing):
   - Enter your API key in the sidebar input field

2. **Via Environment File** (Recommended for production):
   - Create a `.env` file from `.env.example`
   - Add your API key: `GEMINI_API_KEY=your_key_here`

## 📖 Usage Guide

### 1. Register/Login
- Create a new account with username, email, and password
- Login with your credentials

### 2. Dashboard
- View your analysis history
- See statistics (total analyses, average score)
- Click "Start New Analysis" to begin

### 3. Upload Resume
- Upload a PDF resume file
- Paste the target job description
- Optionally add a job title
- Click "Analyze Resume"

### 4. View Results
- See your match score with visual gauge chart
- Review missing skills and keywords
- Get actionable improvement suggestions
- Export report as text file

## 🛡️ Security Features

- **Password Hashing**: All passwords are hashed using SHA-256
- **Session Management**: Secure session state management with Streamlit
- **SQL Injection Protection**: Parameterized queries throughout
- **API Key Security**: API keys stored securely, never in database

## 🎨 Features Breakdown

### Authentication System
- User registration with validation
- Secure password hashing
- Session-based authentication
- Persistent login state

### Resume Analysis
- PDF text extraction (supports pdfminer.six and PyPDF2)
- AI-powered analysis using Gemini 1.5 Flash
- Structured JSON response parsing
- Error handling and validation

### Results Visualization
- Color-coded match scores
- Interactive Plotly gauge charts
- Tabbed interface for organized information
- Downloadable analysis reports

### Database Schema

**Users Table**:
- id (Primary Key)
- username (Unique)
- email
- password_hash
- created_at

**Analysis History Table**:
- id (Primary Key)
- user_id (Foreign Key)
- filename
- match_score
- job_title
- analysis_data
- created_at

## 🔍 How It Works

1. **PDF Processing**: Extracts text from uploaded PDF using pdfminer.six or PyPDF2
2. **AI Analysis**: Sends resume and job description to Gemini API with expert prompt
3. **Structured Response**: Receives JSON with match score, missing skills, summary, and improvements
4. **Data Storage**: Saves analysis to SQLite database for history tracking
5. **Visualization**: Displays results with interactive charts and organized tabs

## 🛠️ Troubleshooting

### Common Issues

**PDF Text Extraction Fails**:
- Ensure PDF is text-based (not scanned image)
- Try re-saving PDF using "Print to PDF" option

**API Key Invalid**:
- Verify API key is correct and active
- Check for extra spaces or characters
- Ensure API is enabled in Google Cloud Console

**Database Errors**:
- Delete `resume_analyzer.db` and restart app
- Check file permissions in project directory

**Gemini API Errors**:
- Check internet connection
- Verify API quota/limits
- Ensure proper API key format

## 📝 Customization

### Modify AI Prompt
Edit the prompt in `utils.py` → `analyze_resume_with_gemini()` function

### Change Scoring Thresholds
Modify score ranges in `app.py` → `results_page()` function

### Database Schema Changes
Update tables in `database.py` → `init_db()` function

## 🚀 Deployment Options

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Add secrets (API key) in dashboard
4. Deploy

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

## 📊 Future Enhancements

- [ ] Multi-format support (DOCX, TXT)
- [ ] Bulk resume analysis
- [ ] Resume template suggestions
- [ ] LinkedIn profile import
- [ ] Email notifications
- [ ] Advanced analytics dashboard
- [ ] Resume version comparison
- [ ] ATS score prediction

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.

## 📄 License

This project is open-source and available for educational and commercial use.

## 🙏 Acknowledgments

- Google Gemini API for AI capabilities
- Streamlit for the web framework
- pdfminer.six for PDF parsing
- Plotly for interactive visualizations

## 📧 Support

For issues or questions, please open an issue in the repository or contact the maintainer.

---

**Built with ❤️ using Streamlit and Google Gemini AI**