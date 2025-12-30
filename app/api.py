"""
Resume ↔ Job Match Analyzer - FastAPI Web Application

A stateless web API for analyzing resumes against job descriptions.

All processing is done in-memory. No data is stored after the request completes.
Temporary files are automatically cleaned up.

Endpoints:
    POST /analyze - Analyze resume against job description
    POST /parse/resume - Parse a resume and return structured data
    POST /parse/job - Parse a job description
    GET /health - Health check endpoint

Usage:
    uvicorn app.api:app --host 0.0.0.0 --port 8000
"""

import tempfile
import os
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .parser.resume_parser import ResumeParser
from .analyzer.job_analyzer import JobDescriptionAnalyzer
from .scorer.match_scorer import MatchScorer
from .report.report_generator import ReportGenerator


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup: nothing to initialize (stateless!)
    yield
    # Shutdown: nothing to clean up


# Create FastAPI application
app = FastAPI(
    title="Resume ↔ Job Match Analyzer",
    description="A privacy-first, stateless resume analysis API. "
                "No data is stored. All processing is done in-memory.",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response Models
class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str


class AnalysisResponse(BaseModel):
    """Analysis result response."""
    success: bool
    overall_score: float
    grade: str
    skill_match_score: float
    experience_score: float
    keyword_coverage_score: float
    ats_score: float
    matched_skills_count: int
    missing_required_count: int
    missing_preferred_count: int
    quick_wins_count: int
    report_format: str
    report: str  # The actual report content


class ParseResumeResponse(BaseModel):
    """Resume parsing response."""
    success: bool
    skills: list
    education_count: int
    experience_count: int
    sections_detected: list
    has_email: bool
    has_phone: bool
    estimated_years: Optional[float]
    ats_friendliness: float


class ParseJobResponse(BaseModel):
    """Job description parsing response."""
    success: bool
    title: str
    seniority: str
    required_skills: list
    preferred_skills: list
    min_years_experience: Optional[float]
    max_years_experience: Optional[float]
    implicit_expectations: list
    culture_signals: list


# Endpoints
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint - redirect to docs."""
    return {"message": "Resume ↔ Job Match Analyzer API. See /docs for documentation."}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns the current status of the API.
    """
    return HealthResponse(
        status="healthy",
        message="Resume analyzer is running. No data is stored."
    )


@app.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    job_description: str = Form(..., description="Job description text"),
    format: str = Form(default="json", description="Report format: json, markdown, or pdf"),
):
    """
    Analyze a resume against a job description.
    
    This endpoint:
    1. Parses the resume file
    2. Analyzes the job description
    3. Calculates match scores
    4. Generates a comprehensive report
    
    **Privacy:** All processing is done in-memory. No data is stored.
    Files are automatically deleted after processing.
    """
    # Validate file type
    filename = resume.filename or "resume.txt"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: .pdf, .docx, .txt"
        )
    
    try:
        # Read file content into memory
        resume_content = await resume.read()
        
        # Parse resume
        resume_parser = ResumeParser()
        resume_data = resume_parser.parse_file(resume_content, filename)
        
        # Parse job description
        job_analyzer = JobDescriptionAnalyzer()
        job_data = job_analyzer.analyze(job_description)
        
        # Calculate match
        scorer = MatchScorer()
        result = scorer.calculate_match(resume_data, job_data)
        
        # Generate report
        generator = ReportGenerator()
        
        if format == "markdown":
            report_content = generator.generate_markdown(result, resume_data, job_data)
            content_type = "text/markdown"
        elif format == "pdf":
            report_content = generator.generate_pdf(result, resume_data, job_data)
            return Response(
                content=report_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": "attachment; filename=analysis_report.pdf"
                }
            )
        else:  # json
            report_content = generator.generate_json(result, resume_data, job_data)
            return JSONResponse(content={
                "success": True,
                "overall_score": result.overall_score,
                "grade": result.overall_grade,
                "skill_match_score": result.skill_match_score.score,
                "experience_score": result.experience_score.score,
                "keyword_coverage_score": result.keyword_coverage_score.score,
                "ats_score": result.ats_score.score,
                "matched_skills_count": len(result.matched_skills),
                "missing_required_count": len(result.missing_required_skills),
                "missing_preferred_count": len(result.missing_preferred_skills),
                "quick_wins_count": len(result.quick_wins),
                "report": report_content,
            })
        
        # Return markdown report
        return Response(
            content=report_content,
            media_type=content_type,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}"
        )
    finally:
        # Ensure file handle is closed
        await resume.close()


@app.post("/parse/resume", response_model=ParseResumeResponse)
async def parse_resume_endpoint(
    resume: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
):
    """
    Parse a resume and return structured data.
    
    This is useful for debugging or integrating with other tools.
    
    **Privacy:** No data is stored after the request completes.
    """
    filename = resume.filename or "resume.txt"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: .pdf, .docx, .txt"
        )
    
    try:
        resume_content = await resume.read()
        
        parser = ResumeParser()
        data = parser.parse_file(resume_content, filename)
        
        return ParseResumeResponse(
            success=True,
            skills=[s.normalized_name for s in data.skills],
            education_count=len(data.education),
            experience_count=len(data.experience),
            sections_detected=data.sections_detected,
            has_email=data.has_email,
            has_phone=data.has_phone,
            estimated_years=data.total_years_experience,
            ats_friendliness=data.estimated_ats_friendliness,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {str(e)}"
        )
    finally:
        await resume.close()


@app.post("/parse/job", response_model=ParseJobResponse)
async def parse_job_endpoint(
    job_description: str = Form(..., description="Job description text"),
):
    """
    Parse a job description and return structured data.
    
    This is useful for debugging or integrating with other tools.
    
    **Privacy:** No data is stored after the request completes.
    """
    try:
        analyzer = JobDescriptionAnalyzer()
        data = analyzer.analyze(job_description)
        
        return ParseJobResponse(
            success=True,
            title=data.title,
            seniority=data.seniority.value if data.seniority else "unknown",
            required_skills=[r.skill.normalized_name for r in data.required_skills],
            preferred_skills=[r.skill.normalized_name for r in data.preferred_skills],
            min_years_experience=data.min_years_experience,
            max_years_experience=data.max_years_experience,
            implicit_expectations=data.implicit_expectations,
            culture_signals=data.culture_signals,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {str(e)}"
        )


# Error handlers
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """Handle unexpected errors."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred",
            "detail": str(exc),
        }
    )
