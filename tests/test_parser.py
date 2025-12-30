"""
Tests for the Resume Parser module.

These tests verify that the parser correctly extracts structured data
from resume text, including skills, education, and experience.
"""

import pytest
from app.parser.resume_parser import ResumeParser, parse_resume_text
from app.models import ResumeData, SkillCategory


class TestResumeParser:
    """Test suite for ResumeParser class."""
    
    @pytest.fixture
    def parser(self):
        """Create a parser instance for tests."""
        return ResumeParser()
    
    @pytest.fixture
    def sample_resume_text(self):
        """Sample resume text for testing."""
        return """
John Doe
john.doe@email.com | (555) 123-4567
linkedin.com/in/johndoe | github.com/johndoe

PROFESSIONAL SUMMARY
Experienced software engineer with 5 years of experience in web development.

WORK EXPERIENCE

Software Engineer at TechCorp | January 2020 - Present
• Developed web applications using React and TypeScript
• Built RESTful APIs with Python and FastAPI
• Improved performance by 40% through optimization

Junior Developer at StartupXYZ | June 2018 - December 2019
• Built features using JavaScript and Node.js
• Worked with PostgreSQL databases

EDUCATION

Bachelor of Science in Computer Science
State University | 2018

SKILLS

Python, JavaScript, TypeScript, React, Node.js, PostgreSQL, Docker, AWS

CERTIFICATIONS

AWS Certified Solutions Architect - Associate | 2022
"""
    
    def test_parse_text_returns_resume_data(self, parser, sample_resume_text):
        """Verify that parse_text returns a ResumeData object."""
        result = parser.parse_text(sample_resume_text)
        assert isinstance(result, ResumeData)
    
    def test_detects_email(self, parser, sample_resume_text):
        """Verify that email detection works."""
        result = parser.parse_text(sample_resume_text)
        assert result.has_email is True
    
    def test_detects_phone(self, parser, sample_resume_text):
        """Verify that phone detection works."""
        result = parser.parse_text(sample_resume_text)
        assert result.has_phone is True
    
    def test_detects_linkedin(self, parser, sample_resume_text):
        """Verify that LinkedIn detection works."""
        result = parser.parse_text(sample_resume_text)
        assert result.has_linkedin is True
    
    def test_detects_github(self, parser, sample_resume_text):
        """Verify that GitHub detection works."""
        result = parser.parse_text(sample_resume_text)
        assert result.has_github is True
    
    def test_extracts_skills(self, parser, sample_resume_text):
        """Verify that skills are extracted."""
        result = parser.parse_text(sample_resume_text)
        assert len(result.skills) > 0
        
        skill_names = [s.normalized_name for s in result.skills]
        assert "Python" in skill_names
        assert "React" in skill_names
    
    def test_detects_sections(self, parser, sample_resume_text):
        """Verify that sections are detected."""
        result = parser.parse_text(sample_resume_text)
        
        assert "experience" in result.sections_detected
        assert "education" in result.sections_detected
        assert "skills" in result.sections_detected
    
    def test_extracts_education(self, parser, sample_resume_text):
        """Verify that education is extracted."""
        result = parser.parse_text(sample_resume_text)
        assert len(result.education) > 0
    
    def test_detects_bullet_points(self, parser, sample_resume_text):
        """Verify that bullet points are detected."""
        result = parser.parse_text(sample_resume_text)
        assert result.has_bullet_points is True
    
    def test_detects_clear_headings(self, parser, sample_resume_text):
        """Verify that clear headings are detected."""
        result = parser.parse_text(sample_resume_text)
        assert result.has_clear_headings is True
    
    def test_estimates_ats_friendliness(self, parser, sample_resume_text):
        """Verify ATS friendliness estimation."""
        result = parser.parse_text(sample_resume_text)
        assert 0 <= result.estimated_ats_friendliness <= 1


class TestSkillNormalization:
    """Test suite for skill normalization."""
    
    @pytest.fixture
    def parser(self):
        return ResumeParser()
    
    def test_normalizes_javascript_variants(self, parser):
        """Verify that JS/JavaScript variants are normalized."""
        text = "Skills: JS, javascript, ECMAScript"
        result = parser.parse_text(text)
        
        skill_names = [s.normalized_name for s in result.skills]
        # All should normalize to "JavaScript"
        assert skill_names.count("JavaScript") >= 1
    
    def test_normalizes_python_variants(self, parser):
        """Verify that Python variants are normalized."""
        text = "Skills: python, Python3, py"
        result = parser.parse_text(text)
        
        skill_names = [s.normalized_name for s in result.skills]
        assert "Python" in skill_names
    
    def test_normalizes_aws_variants(self, parser):
        """Verify that AWS variants are normalized."""
        text = "Skills: AWS, Amazon Web Services"
        result = parser.parse_text(text)
        
        skill_names = [s.normalized_name for s in result.skills]
        assert "Amazon Web Services" in skill_names


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_parse_resume_text_function(self):
        """Verify the convenience function works."""
        text = "Skills: Python, JavaScript, React"
        result = parse_resume_text(text)
        
        assert isinstance(result, ResumeData)
        assert len(result.skills) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def parser(self):
        return ResumeParser()
    
    def test_empty_text(self, parser):
        """Verify handling of empty text."""
        result = parser.parse_text("")
        assert isinstance(result, ResumeData)
        assert len(result.skills) == 0
    
    def test_no_skills_section(self, parser):
        """Verify handling of resume without skills section."""
        text = """
John Doe
john@email.com

Experience:
Worked at Company A doing things.
"""
        result = parser.parse_text(text)
        assert isinstance(result, ResumeData)
    
    def test_unusual_formatting(self, parser):
        """Verify handling of unusual formatting."""
        text = """
JOHN DOE
==========
john@email.com

---SKILLS---
* Python
* JavaScript  
  - React
"""
        result = parser.parse_text(text)
        assert isinstance(result, ResumeData)
        assert result.has_email is True
