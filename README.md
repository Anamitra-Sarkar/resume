# Resume ↔ Job Match Analyzer

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A **privacy-first**, **stateless** resume analysis tool that compares your resume against job descriptions and provides deep, explainable, ATS-aware analysis.

## 🎯 Key Features

- **Privacy First**: No data is stored. All processing happens in-memory.
- **Zero Setup**: No database, no auth, no accounts required.
- **Multiple Formats**: Supports PDF, DOCX, and TXT resumes.
- **Comprehensive Analysis**: 
  - Skill matching (exact, fuzzy, semantic)
  - ATS compatibility checking
  - Experience alignment scoring
  - Keyword coverage analysis
- **Actionable Feedback**: Not generic advice, but specific improvements.
- **Multiple Export Formats**: Markdown, JSON, and PDF reports.
- **Flexible Deployment**: CLI, Web API, or import as a library.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/resume-job-analyzer.git
cd resume-job-analyzer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage (CLI)

```bash
# Analyze a resume against a job description
python -m app.main analyze samples/sample_resume.txt samples/sample_job.txt

# Save report to file
python -m app.main analyze samples/sample_resume.txt samples/sample_job.txt -o report.md

# Generate JSON output
python -m app.main analyze resume.pdf job.txt --format json -o report.json

# Generate PDF report
python -m app.main analyze resume.pdf job.txt --format pdf -o report.pdf
```

### Web API

```bash
# Start the API server
uvicorn app.api:app --host 0.0.0.0 --port 8000

# The API documentation is available at http://localhost:8000/docs
```

### As a Library

```python
from app.parser.resume_parser import parse_resume_text
from app.analyzer.job_analyzer import analyze_job_description
from app.scorer.match_scorer import calculate_match
from app.report.report_generator import generate_markdown_report

# Parse resume and job description
resume_data = parse_resume_text(resume_text)
job_data = analyze_job_description(job_text)

# Calculate match
result = calculate_match(resume_data, job_data)

# Generate report
report = generate_markdown_report(result, resume_data, job_data)
print(report)
```

## 📊 What You Get

### Overall Match Score (0-100)

A weighted score combining:
- **Skill Match (40%)**: How well your skills match requirements
- **Experience (25%)**: Years and relevance of experience
- **Keyword Coverage (20%)**: Important keyword presence
- **ATS Compatibility (15%)**: Resume format analysis

### Detailed Breakdowns

Each score includes:
- How it was calculated
- What affected it positively/negatively
- Specific suggestions for improvement

### Skill Analysis

- ✅ Matched skills (with match type: exact/fuzzy/semantic)
- ❌ Missing required skills
- 📝 Missing preferred skills
- ⚪ Irrelevant skills (in resume but not in job)

### ATS Compatibility Report

- Formatting issues that may affect parsing
- Missing sections or unclear headings
- Keyword coverage gaps
- Specific rewrite suggestions

### Improvement Suggestions

- **Quick Wins**: Easy changes with high impact
- **Long-term Improvements**: Skills to develop
- **Bullet Rewrite Examples**: Before/after examples
- **Skill Placement**: Where to add missing skills

## 📁 Project Structure

```
resume-job-analyzer/
├── app/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── api.py               # FastAPI web application
│   ├── models.py            # Data models
│   ├── knowledge_base.py    # Skill synonyms and categories
│   ├── parser/
│   │   ├── __init__.py
│   │   ├── resume_parser.py # Main resume parser
│   │   ├── pdf_parser.py    # PDF handling
│   │   ├── docx_parser.py   # DOCX handling
│   │   └── txt_parser.py    # Plain text handling
│   ├── analyzer/
│   │   ├── __init__.py
│   │   └── job_analyzer.py  # Job description analyzer
│   ├── scorer/
│   │   ├── __init__.py
│   │   ├── skill_matcher.py # Skill matching engine
│   │   ├── ats_checker.py   # ATS compatibility checker
│   │   └── match_scorer.py  # Main scoring engine
│   └── report/
│       ├── __init__.py
│       └── report_generator.py  # Report generation
├── samples/
│   ├── sample_resume.txt
│   └── sample_job.txt
├── tests/
│   ├── __init__.py
│   ├── test_parser.py
│   ├── test_analyzer.py
│   ├── test_scorer.py
│   └── test_report.py
├── README.md
├── PRIVACY.md
├── requirements.txt
└── LICENSE
```

## 🔧 Configuration

### Custom Weights

You can customize the score weights:

```python
from app.scorer.match_scorer import MatchScorer

custom_weights = {
    'skill_match': 0.50,      # More weight on skills
    'experience': 0.20,
    'keyword_coverage': 0.20,
    'ats': 0.10,
}

scorer = MatchScorer(weights=custom_weights)
result = scorer.calculate_match(resume, job)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_parser.py -v
```

## 📋 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/analyze` | POST | Full analysis (resume file + job text) |
| `/parse/resume` | POST | Parse resume only |
| `/parse/job` | POST | Parse job description only |

## 🔐 Privacy & Security

See [PRIVACY.md](PRIVACY.md) for our complete privacy statement.

**Key guarantees:**
- ❌ No database storage
- ❌ No file persistence after processing
- ❌ No third-party analytics
- ❌ No user accounts or sessions
- ✅ All processing in-memory
- ✅ Temporary files auto-deleted
- ✅ User-initiated downloads only

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [pdfplumber](https://github.com/jsvine/pdfplumber) for PDF parsing
- [python-docx](https://python-docx.readthedocs.io/) for DOCX handling
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [rapidfuzz](https://github.com/maxbachmann/RapidFuzz) for fuzzy matching

---

**Made with ❤️ for job seekers who value privacy**