"""
ATS Compatibility Checker

This module analyzes resumes for ATS (Applicant Tracking System) compatibility.
It detects common issues that cause parsing problems and provides actionable suggestions.

ATS systems typically have trouble with:
- Complex formatting (tables, graphics, columns)
- Non-standard section headers
- Missing keywords
- Unusual file formats
- Poorly structured content

This checker provides:
- Issue detection with severity levels
- Specific suggestions for improvement
- ATS-safe rewrite examples
"""

import re
from typing import Tuple
from dataclasses import dataclass


@dataclass
class ATSIssue:
    """An issue detected that may affect ATS parsing."""
    category: str  # "formatting", "structure", "content", "keywords"
    severity: str  # "high", "medium", "low"
    title: str
    description: str
    suggestion: str
    example: str = ""


@dataclass
class ATSAnalysis:
    """Complete ATS compatibility analysis."""
    score: float  # 0-100
    issues: list  # List[ATSIssue]
    suggestions: list  # List of suggestion strings
    keyword_analysis: dict  # Keyword coverage details


class ATSChecker:
    """
    Analyzes resume for ATS compatibility issues.
    
    The checker examines:
    1. Formatting issues (graphics, tables, complex layouts)
    2. Structure issues (missing sections, unclear headings)
    3. Content issues (missing contact info, vague descriptions)
    4. Keyword coverage (matching job requirements)
    """
    
    # Standard section headers that ATS systems recognize well
    STANDARD_HEADERS = [
        'experience', 'work experience', 'professional experience', 'employment',
        'education', 'academic background',
        'skills', 'technical skills', 'core competencies',
        'summary', 'professional summary', 'objective',
        'certifications', 'certificates', 'credentials',
        'projects', 'personal projects',
    ]
    
    # Optimal section order for most ATS systems
    OPTIMAL_ORDER = ['summary', 'experience', 'skills', 'education', 'certifications', 'projects']
    
    def __init__(self):
        """Initialize the ATS checker."""
        pass
    
    def analyze(
        self, 
        resume_text: str,
        resume_data,  # ResumeData
        job_data,     # JobDescriptionData (optional, for keyword analysis)
        skill_matches: dict  # Results from skill matcher
    ) -> ATSAnalysis:
        """
        Perform complete ATS compatibility analysis.
        
        Args:
            resume_text: Raw resume text
            resume_data: Parsed ResumeData object
            job_data: Parsed JobDescriptionData (for keyword analysis)
            skill_matches: Results from SkillMatcher.match_all_skills()
            
        Returns:
            ATSAnalysis with score, issues, and suggestions
        """
        issues = []
        suggestions = []
        
        # Check formatting issues
        formatting_issues = self._check_formatting(resume_text, resume_data)
        issues.extend(formatting_issues)
        
        # Check structure issues
        structure_issues = self._check_structure(resume_data)
        issues.extend(structure_issues)
        
        # Check content issues
        content_issues = self._check_content(resume_data)
        issues.extend(content_issues)
        
        # Keyword analysis (if job description provided)
        keyword_analysis = {}
        if job_data:
            keyword_issues, keyword_analysis = self._analyze_keywords(
                resume_data, job_data, skill_matches
            )
            issues.extend(keyword_issues)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(issues, skill_matches)
        
        # Calculate overall score
        score = self._calculate_ats_score(issues, resume_data)
        
        return ATSAnalysis(
            score=score,
            issues=issues,
            suggestions=suggestions,
            keyword_analysis=keyword_analysis
        )
    
    def _check_formatting(self, text: str, resume_data) -> list:
        """
        Check for formatting issues that may affect ATS parsing.
        
        Args:
            text: Resume text
            resume_data: Parsed resume data
            
        Returns:
            List of ATSIssue objects
        """
        issues = []
        
        # Check for graphics/images indicator
        if '[Note:' in text and 'image' in text.lower():
            issues.append(ATSIssue(
                category="formatting",
                severity="high",
                title="Graphics/Images Detected",
                description="Your resume appears to contain graphics or images. "
                           "Most ATS systems cannot parse visual elements.",
                suggestion="Remove decorative graphics. Use text-based content only. "
                          "If using icons, replace them with text labels.",
                example="Instead of a star icon for skills, use 'Expert: ' or 'Proficient: '"
            ))
        
        # Check for potential table structures (heuristic)
        # Multiple columns often show up as repeated spacing patterns
        lines_with_many_spaces = sum(
            1 for line in text.split('\n')
            if '    ' in line or '\t\t' in line  # Multiple spaces or tabs
        )
        if lines_with_many_spaces > 5:
            issues.append(ATSIssue(
                category="formatting",
                severity="medium",
                title="Possible Multi-Column Layout",
                description="Your resume may use a multi-column layout. "
                           "ATS systems often parse columns in the wrong order.",
                suggestion="Use a single-column layout for important content. "
                          "If using columns, ensure critical info is in the left column.",
            ))
        
        # Check for special characters that may cause issues
        special_chars = re.findall(r'[^\x00-\x7F]', text)
        if len(special_chars) > 20:  # Some is fine, many is concerning
            issues.append(ATSIssue(
                category="formatting",
                severity="low",
                title="Many Special Characters",
                description="Your resume contains many non-ASCII characters. "
                           "Some ATS systems may not render these correctly.",
                suggestion="Replace special characters with standard alternatives. "
                          "Use simple bullet points (-, *) instead of fancy symbols.",
            ))
        
        return issues
    
    def _check_structure(self, resume_data) -> list:
        """
        Check for structural issues in the resume.
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            List of ATSIssue objects
        """
        issues = []
        
        # Check if key sections are detected
        required_sections = ['experience', 'education', 'skills']
        missing_sections = [
            s for s in required_sections
            if s not in resume_data.sections_detected
        ]
        
        if missing_sections:
            issues.append(ATSIssue(
                category="structure",
                severity="high",
                title="Missing Key Sections",
                description=f"Could not detect: {', '.join(missing_sections)}. "
                           "These sections may be missing or have non-standard headers.",
                suggestion="Use standard section headers that ATS systems recognize.",
                example="Use 'Work Experience' instead of 'My Journey' or 'Career Path'"
            ))
        
        # Check for clear headings
        if not resume_data.has_clear_headings:
            issues.append(ATSIssue(
                category="structure",
                severity="medium",
                title="Unclear Section Headings",
                description="Section headings may not be clearly identifiable. "
                           "ATS systems use headings to categorize content.",
                suggestion="Make section headers prominent and use standard names. "
                          "Each section should start with a clear header on its own line.",
            ))
        
        # Check section order
        if resume_data.section_order:
            expected_first = ['summary', 'experience', 'skills']
            actual_first = resume_data.section_order[0] if resume_data.section_order else ''
            
            if actual_first not in expected_first:
                issues.append(ATSIssue(
                    category="structure",
                    severity="low",
                    title="Non-Standard Section Order",
                    description=f"Resume starts with '{actual_first}'. Most recruiters "
                               "expect Summary or Experience first.",
                    suggestion="Consider starting with a professional summary, "
                              "followed by work experience, then skills and education.",
                ))
        
        return issues
    
    def _check_content(self, resume_data) -> list:
        """
        Check for content issues.
        
        Args:
            resume_data: Parsed resume data
            
        Returns:
            List of ATSIssue objects
        """
        issues = []
        
        # Check contact information
        if not resume_data.has_email:
            issues.append(ATSIssue(
                category="content",
                severity="high",
                title="No Email Address Detected",
                description="Could not find an email address. Recruiters need contact info.",
                suggestion="Add a professional email address at the top of your resume.",
            ))
        
        if not resume_data.has_phone:
            issues.append(ATSIssue(
                category="content",
                severity="medium",
                title="No Phone Number Detected",
                description="Could not find a phone number. Consider adding contact options.",
                suggestion="Add a phone number for recruiters to reach you.",
            ))
        
        # Check skill count
        skill_count = len(resume_data.skills)
        if skill_count < 5:
            issues.append(ATSIssue(
                category="content",
                severity="medium",
                title="Few Skills Listed",
                description=f"Only {skill_count} skills detected. Consider adding more "
                           "relevant skills to improve keyword matching.",
                suggestion="Add a comprehensive skills section with technical skills, "
                          "tools, and relevant competencies.",
            ))
        
        # Check experience entries
        if not resume_data.experience:
            issues.append(ATSIssue(
                category="content",
                severity="high",
                title="No Work Experience Detected",
                description="Could not parse work experience entries. "
                           "This is critical for ATS ranking.",
                suggestion="Structure each job with: Title, Company, Dates, "
                          "and bullet-pointed achievements.",
                example="Software Engineer at TechCorp | Jan 2020 - Present\n"
                       "• Led development of customer-facing features...\n"
                       "• Improved system performance by 40%..."
            ))
        
        # Check bullet points
        if not resume_data.has_bullet_points:
            issues.append(ATSIssue(
                category="content",
                severity="low",
                title="No Bullet Points Detected",
                description="Your resume may not use bullet points for achievements. "
                           "Bullets improve readability and parsing.",
                suggestion="Use bullet points to list achievements and responsibilities. "
                          "Start each bullet with a strong action verb.",
            ))
        
        return issues
    
    def _analyze_keywords(
        self, 
        resume_data, 
        job_data,
        skill_matches: dict
    ) -> Tuple[list, dict]:
        """
        Analyze keyword coverage against job requirements.
        
        Args:
            resume_data: Parsed resume data
            job_data: Parsed job description data
            skill_matches: Results from skill matching
            
        Returns:
            Tuple of (issues list, keyword analysis dict)
        """
        issues = []
        
        # Calculate coverage metrics
        total_required = len(job_data.required_skills)
        total_preferred = len(job_data.preferred_skills)
        
        matched = len(skill_matches.get('matched_skills', []))
        missing_required = len(skill_matches.get('missing_required', []))
        missing_preferred = len(skill_matches.get('missing_preferred', []))
        
        required_coverage = (total_required - missing_required) / total_required if total_required > 0 else 1.0
        
        keyword_analysis = {
            'total_required': total_required,
            'total_preferred': total_preferred,
            'matched_count': matched,
            'missing_required_count': missing_required,
            'missing_preferred_count': missing_preferred,
            'required_coverage': required_coverage,
        }
        
        # Generate issues based on coverage
        if required_coverage < 0.5:
            issues.append(ATSIssue(
                category="keywords",
                severity="high",
                title="Low Keyword Coverage",
                description=f"Your resume matches only {required_coverage*100:.0f}% "
                           f"of required skills. Missing {missing_required} critical keywords.",
                suggestion="Add missing required skills to your skills section. "
                          "Also mention them in relevant job descriptions.",
                example=self._format_missing_skills(skill_matches.get('missing_required', [])[:5])
            ))
        elif required_coverage < 0.75:
            issues.append(ATSIssue(
                category="keywords",
                severity="medium",
                title="Moderate Keyword Coverage",
                description=f"Your resume matches {required_coverage*100:.0f}% "
                           f"of required skills. Consider adding more keywords.",
                suggestion="Review missing skills and add those you have experience with.",
                example=self._format_missing_skills(skill_matches.get('missing_required', [])[:3])
            ))
        
        # Check for keyword stuffing (too many skills relative to experience)
        if len(resume_data.skills) > 50:
            issues.append(ATSIssue(
                category="keywords",
                severity="medium",
                title="Possible Keyword Stuffing",
                description=f"Your resume lists {len(resume_data.skills)} skills. "
                           "ATS systems may flag excessive keyword lists.",
                suggestion="Focus on skills you can demonstrate with experience. "
                          "Quality over quantity.",
            ))
        
        return issues, keyword_analysis
    
    def _format_missing_skills(self, missing_requirements: list) -> str:
        """Format missing skills as example text."""
        if not missing_requirements:
            return ""
        skill_names = [req.skill.normalized_name for req in missing_requirements]
        return "Missing: " + ", ".join(skill_names)
    
    def _generate_suggestions(self, issues: list, skill_matches: dict) -> list:
        """
        Generate prioritized suggestions based on issues.
        
        Args:
            issues: List of ATSIssue objects
            skill_matches: Skill matching results
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Prioritize high-severity issues
        high_severity = [i for i in issues if i.severity == "high"]
        for issue in high_severity:
            suggestions.append(f"[HIGH PRIORITY] {issue.suggestion}")
        
        # Add skill-specific suggestions
        missing_required = skill_matches.get('missing_required', [])
        if missing_required:
            skill_list = [r.skill.normalized_name for r in missing_required[:5]]
            suggestions.append(
                f"Add these required skills if you have them: {', '.join(skill_list)}"
            )
        
        # Medium severity suggestions
        medium_severity = [i for i in issues if i.severity == "medium"]
        for issue in medium_severity[:3]:  # Limit to avoid overwhelming
            suggestions.append(issue.suggestion)
        
        return suggestions
    
    def _calculate_ats_score(self, issues: list, resume_data) -> float:
        """
        Calculate overall ATS compatibility score.
        
        Scoring:
        - Start at 100
        - Deduct points for each issue based on severity
        - Floor at 0
        
        Args:
            issues: List of detected issues
            resume_data: Parsed resume data
            
        Returns:
            Score from 0 to 100
        """
        score = 100.0
        
        severity_penalties = {
            'high': 15,
            'medium': 8,
            'low': 3,
        }
        
        for issue in issues:
            score -= severity_penalties.get(issue.severity, 5)
        
        # Bonus points for good practices
        if resume_data.has_bullet_points:
            score += 5
        if resume_data.has_clear_headings:
            score += 5
        if len(resume_data.sections_detected) >= 4:
            score += 5
        
        return max(0, min(100, score))


# Convenience function
def check_ats_compatibility(
    resume_text: str,
    resume_data,
    job_data=None,
    skill_matches=None
) -> ATSAnalysis:
    """
    Check resume for ATS compatibility issues.
    
    Args:
        resume_text: Raw resume text
        resume_data: Parsed ResumeData
        job_data: Optional JobDescriptionData
        skill_matches: Optional skill matching results
        
    Returns:
        ATSAnalysis with score and issues
    """
    checker = ATSChecker()
    return checker.analyze(
        resume_text,
        resume_data,
        job_data,
        skill_matches or {}
    )
