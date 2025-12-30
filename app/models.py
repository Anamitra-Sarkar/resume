"""
Resume Job Match Analyzer - Core Data Models

This module defines the data structures used throughout the application.
All models use dataclasses for simplicity and clarity.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class SkillCategory(str, Enum):
    """Categories for skills extracted from resumes/job descriptions."""
    HARD = "hard"           # Technical skills (programming, tools)
    SOFT = "soft"           # Interpersonal skills (communication, leadership)
    TOOL = "tool"           # Specific tools/software
    CERTIFICATION = "certification"
    LANGUAGE = "language"   # Programming or human languages


class RequirementLevel(str, Enum):
    """How critical a skill/requirement is for the job."""
    REQUIRED = "required"
    PREFERRED = "preferred"
    NICE_TO_HAVE = "nice_to_have"


class SeniorityLevel(str, Enum):
    """Detected seniority level from job description."""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"
    UNKNOWN = "unknown"


@dataclass
class Skill:
    """Represents a skill extracted from resume or job description."""
    name: str
    category: SkillCategory = SkillCategory.HARD
    normalized_name: str = ""  # Canonical form (e.g., "JavaScript" for "JS")
    years_experience: Optional[float] = None  # Estimated years of experience
    proficiency: Optional[str] = None  # e.g., "expert", "intermediate"
    context: str = ""  # Where this skill was mentioned
    mention_count: int = 1  # How many times mentioned
    
    def __post_init__(self):
        if not self.normalized_name:
            self.normalized_name = self.name


@dataclass
class Education:
    """Educational qualification from resume."""
    degree: str
    field_of_study: str = ""
    institution: str = ""
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    honors: str = ""


@dataclass
class WorkExperience:
    """Work experience entry from resume."""
    title: str
    company: str = ""
    start_date: str = ""  # Keep as string for flexibility
    end_date: str = ""    # "Present" for current jobs
    duration_months: Optional[int] = None
    description: str = ""
    skills_used: list = field(default_factory=list)
    achievements: list = field(default_factory=list)


@dataclass
class Certification:
    """Professional certification from resume."""
    name: str
    issuer: str = ""
    date_obtained: str = ""
    expiry_date: str = ""
    credential_id: str = ""


@dataclass
class ResumeData:
    """Structured data extracted from a resume."""
    raw_text: str = ""
    
    # Contact info (not stored, just detected for format analysis)
    has_email: bool = False
    has_phone: bool = False
    has_linkedin: bool = False
    has_github: bool = False
    
    # Core sections
    skills: list = field(default_factory=list)  # List[Skill]
    education: list = field(default_factory=list)  # List[Education]
    experience: list = field(default_factory=list)  # List[WorkExperience]
    certifications: list = field(default_factory=list)  # List[Certification]
    
    # Section detection results
    sections_detected: list = field(default_factory=list)  # e.g., ["experience", "skills", "education"]
    section_order: list = field(default_factory=list)  # Order sections appear
    
    # Summary/objective if present
    summary: str = ""
    
    # Years of experience (total estimated)
    total_years_experience: Optional[float] = None
    
    # Format quality indicators
    has_clear_headings: bool = False
    has_bullet_points: bool = False
    estimated_ats_friendliness: float = 0.5  # 0-1 scale


@dataclass
class JobRequirement:
    """A requirement extracted from a job description."""
    skill: Skill
    level: RequirementLevel = RequirementLevel.REQUIRED
    years_required: Optional[float] = None
    context: str = ""  # Original text mentioning this requirement


@dataclass
class JobDescriptionData:
    """Structured data extracted from a job description."""
    raw_text: str = ""
    
    # Role information
    title: str = ""
    seniority: SeniorityLevel = SeniorityLevel.UNKNOWN
    department: str = ""
    
    # Requirements
    required_skills: list = field(default_factory=list)  # List[JobRequirement]
    preferred_skills: list = field(default_factory=list)  # List[JobRequirement]
    
    # Education requirements
    degree_required: Optional[str] = None
    degree_preferred: Optional[str] = None
    
    # Experience requirements
    min_years_experience: Optional[float] = None
    max_years_experience: Optional[float] = None
    
    # Implicit expectations (detected from phrases like "fast-paced")
    implicit_expectations: list = field(default_factory=list)
    
    # Company culture signals
    culture_signals: list = field(default_factory=list)


@dataclass
class SkillMatch:
    """Result of matching a resume skill against job requirements."""
    resume_skill: Skill
    job_requirement: Optional[JobRequirement] = None
    match_type: str = "none"  # "exact", "fuzzy", "semantic", "none"
    match_score: float = 0.0  # 0-1 confidence
    explanation: str = ""


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of a single score component."""
    score: float  # 0-100
    weight: float  # Weight used in overall calculation
    explanation: str
    positive_factors: list = field(default_factory=list)
    negative_factors: list = field(default_factory=list)
    improvement_suggestions: list = field(default_factory=list)


@dataclass
class MatchResult:
    """Complete analysis result comparing resume to job description."""
    # Overall score
    overall_score: float  # 0-100
    overall_grade: str  # A, B, C, D, F
    
    # Score components
    skill_match_score: ScoreBreakdown = field(default_factory=lambda: ScoreBreakdown(0, 0.4, ""))
    experience_score: ScoreBreakdown = field(default_factory=lambda: ScoreBreakdown(0, 0.25, ""))
    keyword_coverage_score: ScoreBreakdown = field(default_factory=lambda: ScoreBreakdown(0, 0.2, ""))
    ats_score: ScoreBreakdown = field(default_factory=lambda: ScoreBreakdown(0, 0.15, ""))
    
    # Matched items
    matched_skills: list = field(default_factory=list)  # List[SkillMatch]
    missing_required_skills: list = field(default_factory=list)  # Skills job wants but resume lacks
    missing_preferred_skills: list = field(default_factory=list)
    irrelevant_skills: list = field(default_factory=list)  # Resume skills not in job
    
    # ATS analysis
    ats_issues: list = field(default_factory=list)
    ats_suggestions: list = field(default_factory=list)
    
    # Improvement suggestions
    quick_wins: list = field(default_factory=list)  # Easy changes with high impact
    long_term_improvements: list = field(default_factory=list)
    skill_placement_suggestions: list = field(default_factory=list)
    bullet_rewrite_examples: list = field(default_factory=list)


@dataclass
class ImprovementSuggestion:
    """A specific suggestion for improving the resume."""
    category: str  # "skill", "formatting", "keyword", "structure"
    priority: str  # "high", "medium", "low"
    title: str
    description: str
    example: str = ""  # Optional example of implementation
    affected_section: str = ""  # Which resume section to modify
