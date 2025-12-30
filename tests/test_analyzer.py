"""
Tests for the Job Description Analyzer module.

These tests verify that the analyzer correctly extracts structured data
from job descriptions, including required/preferred skills and experience levels.
"""

import pytest
from app.analyzer.job_analyzer import JobDescriptionAnalyzer, analyze_job_description
from app.models import JobDescriptionData, SeniorityLevel, RequirementLevel


class TestJobDescriptionAnalyzer:
    """Test suite for JobDescriptionAnalyzer class."""
    
    @pytest.fixture
    def analyzer(self):
        """Create an analyzer instance for tests."""
        return JobDescriptionAnalyzer()
    
    @pytest.fixture
    def sample_job_text(self):
        """Sample job description for testing."""
        return """
Senior Software Engineer

We are looking for an experienced Senior Software Engineer to join our team.

Requirements:
- 5+ years of experience in software development
- Strong proficiency in Python and JavaScript
- Experience with React or Angular
- Knowledge of PostgreSQL and MongoDB
- Experience with AWS or GCP
- Bachelor's degree in Computer Science

Nice to Have:
- Experience with Docker and Kubernetes
- Familiarity with GraphQL
- Open source contributions

This is a fast-paced environment where you'll take ownership of projects.
"""
    
    def test_analyze_returns_job_description_data(self, analyzer, sample_job_text):
        """Verify that analyze returns a JobDescriptionData object."""
        result = analyzer.analyze(sample_job_text)
        assert isinstance(result, JobDescriptionData)
    
    def test_extracts_job_title(self, analyzer, sample_job_text):
        """Verify that job title is extracted."""
        result = analyzer.analyze(sample_job_text)
        assert "Software Engineer" in result.title
    
    def test_detects_seniority_level(self, analyzer, sample_job_text):
        """Verify that seniority level is detected."""
        result = analyzer.analyze(sample_job_text)
        assert result.seniority == SeniorityLevel.SENIOR
    
    def test_extracts_required_skills(self, analyzer, sample_job_text):
        """Verify that required skills are extracted."""
        result = analyzer.analyze(sample_job_text)
        
        required_skill_names = [r.skill.normalized_name for r in result.required_skills]
        assert "Python" in required_skill_names
        assert "JavaScript" in required_skill_names
    
    def test_extracts_preferred_skills(self, analyzer, sample_job_text):
        """Verify that preferred skills are extracted."""
        result = analyzer.analyze(sample_job_text)
        
        preferred_skill_names = [r.skill.normalized_name for r in result.preferred_skills]
        assert "Docker" in preferred_skill_names
    
    def test_extracts_experience_requirements(self, analyzer, sample_job_text):
        """Verify that experience requirements are extracted."""
        result = analyzer.analyze(sample_job_text)
        assert result.min_years_experience == 5.0
    
    def test_detects_implicit_expectations(self, analyzer, sample_job_text):
        """Verify that implicit expectations are detected."""
        result = analyzer.analyze(sample_job_text)
        
        # "fast-paced" and "ownership" should be detected
        assert "fast_paced" in result.implicit_expectations
        assert "ownership" in result.implicit_expectations
    
    def test_stores_raw_text(self, analyzer, sample_job_text):
        """Verify that raw text is stored."""
        result = analyzer.analyze(sample_job_text)
        assert result.raw_text == sample_job_text


class TestSeniorityDetection:
    """Test seniority level detection."""
    
    @pytest.fixture
    def analyzer(self):
        return JobDescriptionAnalyzer()
    
    def test_detects_junior_level(self, analyzer):
        """Verify junior level detection."""
        text = "Junior Developer - Entry level position, 0-2 years experience"
        result = analyzer.analyze(text)
        assert result.seniority in [SeniorityLevel.JUNIOR, SeniorityLevel.ENTRY]
    
    def test_detects_mid_level(self, analyzer):
        """Verify mid-level detection."""
        text = "Software Engineer - 3-5 years experience required"
        result = analyzer.analyze(text)
        assert result.seniority == SeniorityLevel.MID
    
    def test_detects_senior_level(self, analyzer):
        """Verify senior level detection."""
        text = "Senior Engineer - 5+ years of extensive experience"
        result = analyzer.analyze(text)
        assert result.seniority == SeniorityLevel.SENIOR
    
    def test_detects_lead_level(self, analyzer):
        """Verify lead level detection."""
        text = "Tech Lead / Team Lead - 8+ years, leadership experience"
        result = analyzer.analyze(text)
        assert result.seniority == SeniorityLevel.LEAD


class TestExperienceExtraction:
    """Test experience requirement extraction."""
    
    @pytest.fixture
    def analyzer(self):
        return JobDescriptionAnalyzer()
    
    def test_extracts_minimum_years(self, analyzer):
        """Verify minimum years extraction."""
        text = "Must have at least 3 years of experience"
        result = analyzer.analyze(text)
        assert result.min_years_experience == 3.0
    
    def test_extracts_range(self, analyzer):
        """Verify range extraction."""
        text = "3-5 years of experience in software development"
        result = analyzer.analyze(text)
        assert result.min_years_experience == 3.0
        assert result.max_years_experience == 5.0
    
    def test_extracts_plus_format(self, analyzer):
        """Verify 5+ format extraction."""
        text = "5+ years experience required"
        result = analyzer.analyze(text)
        assert result.min_years_experience == 5.0


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_analyze_job_description_function(self):
        """Verify the convenience function works."""
        text = "Looking for Python developer with 3+ years experience"
        result = analyze_job_description(text)
        
        assert isinstance(result, JobDescriptionData)
        assert result.min_years_experience == 3.0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def analyzer(self):
        return JobDescriptionAnalyzer()
    
    def test_empty_text(self, analyzer):
        """Verify handling of empty text."""
        result = analyzer.analyze("")
        assert isinstance(result, JobDescriptionData)
    
    def test_no_requirements_section(self, analyzer):
        """Verify handling of job without explicit requirements."""
        text = """
Software Engineer

We're building cool stuff. Join us!
Work with Python and JavaScript.
"""
        result = analyzer.analyze(text)
        assert isinstance(result, JobDescriptionData)
    
    def test_mixed_case_skills(self, analyzer):
        """Verify handling of mixed case skill names."""
        text = """
Requirements:
- PYTHON
- javascript
- React.js
"""
        result = analyzer.analyze(text)
        skill_names = [r.skill.normalized_name for r in result.required_skills]
        assert "Python" in skill_names
        assert "JavaScript" in skill_names
        assert "React" in skill_names
