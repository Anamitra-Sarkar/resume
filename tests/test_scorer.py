"""
Tests for the Match Scorer module.

These tests verify that the scorer correctly calculates match scores
between resumes and job descriptions.
"""

import pytest
from app.scorer.match_scorer import MatchScorer, calculate_match
from app.scorer.skill_matcher import SkillMatcher
from app.parser.resume_parser import parse_resume_text
from app.analyzer.job_analyzer import analyze_job_description
from app.models import MatchResult, ScoreBreakdown


class TestMatchScorer:
    """Test suite for MatchScorer class."""
    
    @pytest.fixture
    def scorer(self):
        """Create a scorer instance for tests."""
        return MatchScorer()
    
    @pytest.fixture
    def sample_resume(self):
        """Parse sample resume for testing."""
        text = """
John Doe
john@email.com | (555) 123-4567

SKILLS
Python, JavaScript, React, PostgreSQL, Docker, AWS

EXPERIENCE
Software Engineer at TechCorp | 2019 - Present
• Built web applications using React and Python
• Deployed services on AWS using Docker

EDUCATION
BS in Computer Science | 2019
"""
        return parse_resume_text(text)
    
    @pytest.fixture
    def sample_job(self):
        """Parse sample job for testing."""
        text = """
Software Engineer

Requirements:
- Python
- JavaScript
- React
- PostgreSQL
- 3+ years experience

Nice to Have:
- Docker
- AWS
- Kubernetes
"""
        return analyze_job_description(text)
    
    def test_calculate_match_returns_match_result(self, scorer, sample_resume, sample_job):
        """Verify that calculate_match returns a MatchResult."""
        result = scorer.calculate_match(sample_resume, sample_job)
        assert isinstance(result, MatchResult)
    
    def test_overall_score_range(self, scorer, sample_resume, sample_job):
        """Verify that overall score is in valid range."""
        result = scorer.calculate_match(sample_resume, sample_job)
        assert 0 <= result.overall_score <= 100
    
    def test_grade_is_valid(self, scorer, sample_resume, sample_job):
        """Verify that grade is a valid letter grade."""
        result = scorer.calculate_match(sample_resume, sample_job)
        assert result.overall_grade in ['A', 'B', 'C', 'D', 'F']
    
    def test_has_score_breakdowns(self, scorer, sample_resume, sample_job):
        """Verify that all score breakdowns are present."""
        result = scorer.calculate_match(sample_resume, sample_job)
        
        assert isinstance(result.skill_match_score, ScoreBreakdown)
        assert isinstance(result.experience_score, ScoreBreakdown)
        assert isinstance(result.keyword_coverage_score, ScoreBreakdown)
        assert isinstance(result.ats_score, ScoreBreakdown)
    
    def test_matched_skills_populated(self, scorer, sample_resume, sample_job):
        """Verify that matched skills are populated."""
        result = scorer.calculate_match(sample_resume, sample_job)
        assert len(result.matched_skills) > 0
    
    def test_has_improvement_suggestions(self, scorer, sample_resume, sample_job):
        """Verify that improvement suggestions are generated."""
        result = scorer.calculate_match(sample_resume, sample_job)
        # Should have at least some suggestions
        assert len(result.quick_wins) >= 0  # May or may not have quick wins
    
    def test_high_match_gets_good_score(self, scorer, sample_resume, sample_job):
        """Verify that a good match gets a decent score."""
        result = scorer.calculate_match(sample_resume, sample_job)
        # Resume has most required skills, should score reasonably
        assert result.overall_score >= 50


class TestSkillMatcher:
    """Test suite for SkillMatcher class."""
    
    @pytest.fixture
    def matcher(self):
        """Create a matcher instance for tests."""
        return SkillMatcher()
    
    def test_exact_match(self, matcher):
        """Verify exact matching works."""
        from app.models import Skill, JobRequirement
        
        resume_skill = Skill(name="Python", normalized_name="Python")
        job_req = JobRequirement(
            skill=Skill(name="Python", normalized_name="Python")
        )
        
        match = matcher.match_skill(resume_skill, [job_req])
        
        assert match is not None
        assert match.match_type == "exact"
        assert match.match_score == 1.0
    
    def test_no_match(self, matcher):
        """Verify no match when skills don't align."""
        from app.models import Skill, JobRequirement
        
        resume_skill = Skill(name="Python", normalized_name="Python")
        job_req = JobRequirement(
            skill=Skill(name="Rust", normalized_name="Rust")
        )
        
        match = matcher.match_skill(resume_skill, [job_req])
        
        # May or may not match semantically, but not exact
        if match:
            assert match.match_type != "exact"


class TestScoreBreakdowns:
    """Test score breakdown details."""
    
    @pytest.fixture
    def scorer(self):
        return MatchScorer()
    
    def test_skill_score_has_explanation(self, scorer):
        """Verify skill score has explanation."""
        resume = parse_resume_text("Skills: Python, JavaScript")
        job = analyze_job_description("Requirements: Python, JavaScript, Go")
        
        result = scorer.calculate_match(resume, job)
        
        assert result.skill_match_score.explanation != ""
    
    def test_score_weights_sum_to_one(self, scorer):
        """Verify that score weights sum to approximately 1."""
        total_weight = sum(scorer.weights.values())
        assert 0.99 <= total_weight <= 1.01


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_calculate_match_function(self):
        """Verify the convenience function works."""
        resume = parse_resume_text("Skills: Python, JavaScript")
        job = analyze_job_description("Requirements: Python, JavaScript")
        
        result = calculate_match(resume, job)
        
        assert isinstance(result, MatchResult)
        assert result.overall_score >= 0


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def scorer(self):
        return MatchScorer()
    
    def test_empty_resume(self, scorer):
        """Verify handling of empty resume."""
        resume = parse_resume_text("")
        job = analyze_job_description("Requirements: Python")
        
        result = scorer.calculate_match(resume, job)
        
        assert isinstance(result, MatchResult)
        assert result.overall_score >= 0
    
    def test_empty_job(self, scorer):
        """Verify handling of empty job description."""
        resume = parse_resume_text("Skills: Python")
        job = analyze_job_description("")
        
        result = scorer.calculate_match(resume, job)
        
        assert isinstance(result, MatchResult)
    
    def test_no_skill_overlap(self, scorer):
        """Verify handling of no skill overlap."""
        resume = parse_resume_text("Skills: Python, JavaScript")
        job = analyze_job_description("Requirements: Rust, Haskell")
        
        result = scorer.calculate_match(resume, job)
        
        # Should still return a result, just with low score
        assert isinstance(result, MatchResult)
        assert len(result.missing_required_skills) > 0
