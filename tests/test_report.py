"""
Tests for the Report Generator module.

These tests verify that reports are generated correctly in various formats.
"""

import pytest
import json
from app.report.report_generator import (
    ReportGenerator, 
    generate_markdown_report,
    generate_json_report
)
from app.parser.resume_parser import parse_resume_text
from app.analyzer.job_analyzer import analyze_job_description
from app.scorer.match_scorer import calculate_match


class TestReportGenerator:
    """Test suite for ReportGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a generator instance for tests."""
        return ReportGenerator()
    
    @pytest.fixture
    def sample_result(self):
        """Generate a sample match result for testing."""
        resume = parse_resume_text("""
John Doe
john@email.com

SKILLS
Python, JavaScript, React, PostgreSQL

EXPERIENCE
Software Engineer at TechCorp | 2020 - Present
• Built web applications

EDUCATION
BS Computer Science | 2020
""")
        job = analyze_job_description("""
Software Engineer

Requirements:
- Python
- JavaScript
- 3+ years experience

Nice to Have:
- React
- Docker
""")
        return calculate_match(resume, job), resume, job
    
    def test_generate_markdown_returns_string(self, generator, sample_result):
        """Verify that markdown generation returns a string."""
        result, resume, job = sample_result
        report = generator.generate_markdown(result, resume, job)
        assert isinstance(report, str)
        assert len(report) > 0
    
    def test_markdown_has_title(self, generator, sample_result):
        """Verify that markdown report has a title."""
        result, resume, job = sample_result
        report = generator.generate_markdown(result, resume, job)
        assert "# Resume ↔ Job Match Analysis Report" in report
    
    def test_markdown_has_score(self, generator, sample_result):
        """Verify that markdown report includes the score."""
        result, resume, job = sample_result
        report = generator.generate_markdown(result, resume, job)
        assert "Overall Match Score" in report
        assert str(int(result.overall_score)) in report
    
    def test_markdown_has_sections(self, generator, sample_result):
        """Verify that markdown report has expected sections."""
        result, resume, job = sample_result
        report = generator.generate_markdown(result, resume, job)
        
        assert "Executive Summary" in report
        assert "Score Breakdown" in report
        assert "Skill Analysis" in report
        assert "ATS Compatibility" in report
        assert "Improvement Suggestions" in report
    
    def test_generate_json_returns_valid_json(self, generator, sample_result):
        """Verify that JSON generation returns valid JSON."""
        result, resume, job = sample_result
        report = generator.generate_json(result, resume, job)
        
        # Should be valid JSON
        data = json.loads(report)
        assert isinstance(data, dict)
    
    def test_json_has_required_fields(self, generator, sample_result):
        """Verify that JSON report has required fields."""
        result, resume, job = sample_result
        report = generator.generate_json(result, resume, job)
        data = json.loads(report)
        
        assert "summary" in data
        assert "overall_score" in data["summary"]
        assert "grade" in data["summary"]
        assert "scores" in data
        assert "skills" in data
        assert "improvements" in data
    
    def test_json_scores_match_result(self, generator, sample_result):
        """Verify that JSON scores match the result object."""
        result, resume, job = sample_result
        report = generator.generate_json(result, resume, job)
        data = json.loads(report)
        
        assert data["summary"]["overall_score"] == result.overall_score
        assert data["summary"]["grade"] == result.overall_grade


class TestMarkdownDetails:
    """Test detailed markdown content."""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    @pytest.fixture
    def result_with_missing(self):
        """Generate a result with missing skills."""
        resume = parse_resume_text("Skills: Python")
        job = analyze_job_description("""
Requirements:
- Python
- JavaScript
- React
- Node.js
""")
        return calculate_match(resume, job), resume, job
    
    def test_shows_missing_skills(self, generator, result_with_missing):
        """Verify that missing skills are shown."""
        result, resume, job = result_with_missing
        report = generator.generate_markdown(result, resume, job)
        
        assert "Missing Required Skills" in report
    
    def test_shows_matched_skills(self, generator, result_with_missing):
        """Verify that matched skills are shown."""
        result, resume, job = result_with_missing
        report = generator.generate_markdown(result, resume, job)
        
        # Should show Python as matched
        assert "Matched Skills" in report or "matched" in report.lower()


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    @pytest.fixture
    def sample_data(self):
        resume = parse_resume_text("Skills: Python, JavaScript")
        job = analyze_job_description("Requirements: Python")
        result = calculate_match(resume, job)
        return result, resume, job
    
    def test_generate_markdown_report_function(self, sample_data):
        """Verify the markdown convenience function works."""
        result, resume, job = sample_data
        report = generate_markdown_report(result, resume, job)
        
        assert isinstance(report, str)
        assert len(report) > 0
    
    def test_generate_json_report_function(self, sample_data):
        """Verify the JSON convenience function works."""
        result, resume, job = sample_data
        report = generate_json_report(result, resume, job)
        
        data = json.loads(report)
        assert isinstance(data, dict)


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def generator(self):
        return ReportGenerator()
    
    def test_empty_match_result(self, generator):
        """Verify handling of minimal/empty match result."""
        resume = parse_resume_text("")
        job = analyze_job_description("")
        result = calculate_match(resume, job)
        
        # Should not raise an error
        report = generator.generate_markdown(result, resume, job)
        assert isinstance(report, str)
    
    def test_brief_report_option(self, generator):
        """Verify brief report option works."""
        resume = parse_resume_text("Skills: Python")
        job = analyze_job_description("Requirements: Python")
        result = calculate_match(resume, job)
        
        full_report = generator.generate_markdown(result, resume, job, include_details=True)
        brief_report = generator.generate_markdown(result, resume, job, include_details=False)
        
        # Brief should be shorter or equal
        assert len(brief_report) <= len(full_report)
