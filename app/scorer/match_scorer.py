"""
Match Scoring Engine

This module calculates comprehensive match scores between a resume and job description.
It produces explainable scores across multiple dimensions:

1. Skill Match Score - How well resume skills match job requirements
2. Experience Score - Years and relevance of experience
3. Keyword Coverage Score - Coverage of important keywords
4. ATS Score - Compatibility with ATS systems

Each score includes:
- The numeric score (0-100)
- Explanation of how it was calculated
- Factors that affected it positively/negatively
- Suggestions for improvement
"""

from typing import Optional

from ..models import (
    ResumeData, JobDescriptionData, MatchResult, 
    ScoreBreakdown, ImprovementSuggestion, SeniorityLevel
)
from .skill_matcher import SkillMatcher
from .ats_checker import ATSChecker


class MatchScorer:
    """
    Calculates comprehensive match scores between resume and job description.
    
    The scorer uses a weighted combination of multiple factors:
    - Skill matching (40% weight)
    - Experience alignment (25% weight)
    - Keyword coverage (20% weight)
    - ATS compatibility (15% weight)
    
    All scoring is deterministic and reproducible.
    """
    
    # Default weights for score components
    DEFAULT_WEIGHTS = {
        'skill_match': 0.40,
        'experience': 0.25,
        'keyword_coverage': 0.20,
        'ats': 0.15,
    }
    
    # Grade thresholds
    GRADE_THRESHOLDS = {
        'A': 90,
        'B': 75,
        'C': 60,
        'D': 45,
        'F': 0,
    }
    
    def __init__(self, weights: dict = None):
        """
        Initialize the scorer.
        
        Args:
            weights: Optional custom weights for score components
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.skill_matcher = SkillMatcher()
        self.ats_checker = ATSChecker()
    
    def calculate_match(
        self,
        resume: ResumeData,
        job: JobDescriptionData
    ) -> MatchResult:
        """
        Calculate complete match between resume and job description.
        
        Args:
            resume: Parsed resume data
            job: Parsed job description data
            
        Returns:
            MatchResult with all scores and suggestions
        """
        # Step 1: Match skills
        skill_matches = self.skill_matcher.match_all_skills(
            resume.skills,
            job.required_skills,
            job.preferred_skills
        )
        
        # Step 2: Calculate individual scores
        skill_score = self._calculate_skill_score(skill_matches, job)
        experience_score = self._calculate_experience_score(resume, job)
        keyword_score = self._calculate_keyword_score(skill_matches, job)
        
        # Step 3: ATS analysis
        ats_analysis = self.ats_checker.analyze(
            resume.raw_text,
            resume,
            job,
            skill_matches
        )
        ats_score = self._create_ats_score_breakdown(ats_analysis)
        
        # Step 4: Calculate overall score
        overall_score = self._calculate_overall_score(
            skill_score, experience_score, keyword_score, ats_score
        )
        
        # Step 5: Determine grade
        grade = self._calculate_grade(overall_score)
        
        # Step 6: Generate improvement suggestions
        quick_wins, long_term = self._generate_improvement_suggestions(
            resume, job, skill_matches, ats_analysis
        )
        
        # Step 7: Generate bullet rewrite examples
        bullet_examples = self._generate_bullet_examples(
            resume, job, skill_matches
        )
        
        # Step 8: Generate skill placement suggestions
        placement_suggestions = self._generate_placement_suggestions(
            skill_matches, resume
        )
        
        return MatchResult(
            overall_score=overall_score,
            overall_grade=grade,
            skill_match_score=skill_score,
            experience_score=experience_score,
            keyword_coverage_score=keyword_score,
            ats_score=ats_score,
            matched_skills=skill_matches.get('matched_skills', []),
            missing_required_skills=[r.skill for r in skill_matches.get('missing_required', [])],
            missing_preferred_skills=[r.skill for r in skill_matches.get('missing_preferred', [])],
            irrelevant_skills=skill_matches.get('irrelevant_skills', []),
            ats_issues=ats_analysis.issues,
            ats_suggestions=ats_analysis.suggestions,
            quick_wins=quick_wins,
            long_term_improvements=long_term,
            skill_placement_suggestions=placement_suggestions,
            bullet_rewrite_examples=bullet_examples,
        )
    
    def _calculate_skill_score(self, skill_matches: dict, job: JobDescriptionData) -> ScoreBreakdown:
        """
        Calculate skill match score.
        
        Factors:
        - Required skill coverage (most important)
        - Preferred skill coverage (bonus)
        - Match quality (exact > fuzzy > semantic)
        
        Args:
            skill_matches: Results from skill matcher
            job: Job description data
            
        Returns:
            ScoreBreakdown with explanation
        """
        matched = skill_matches.get('matched_skills', [])
        missing_required = skill_matches.get('missing_required', [])
        missing_preferred = skill_matches.get('missing_preferred', [])
        
        total_required = len(job.required_skills)
        total_preferred = len(job.preferred_skills)
        
        # Calculate required skill coverage
        matched_required = sum(
            1 for m in matched 
            if m.job_requirement and m.job_requirement.skill.normalized_name in 
            {r.skill.normalized_name for r in job.required_skills}
        )
        
        if total_required > 0:
            required_coverage = matched_required / total_required
        else:
            required_coverage = 1.0
        
        # Calculate preferred skill coverage (less weight)
        matched_preferred = sum(
            1 for m in matched
            if m.job_requirement and m.job_requirement.skill.normalized_name in
            {r.skill.normalized_name for r in job.preferred_skills}
        )
        
        if total_preferred > 0:
            preferred_coverage = matched_preferred / total_preferred
        else:
            preferred_coverage = 0.0
        
        # Calculate match quality bonus
        exact_matches = sum(1 for m in matched if m.match_type == "exact")
        fuzzy_matches = sum(1 for m in matched if m.match_type == "fuzzy")
        semantic_matches = sum(1 for m in matched if m.match_type == "semantic")
        
        # Base score on required coverage (70%) + preferred (20%) + quality (10%)
        base_score = required_coverage * 70
        preferred_bonus = preferred_coverage * 20
        
        total_matches = len(matched)
        if total_matches > 0:
            quality_bonus = ((exact_matches * 1.0 + fuzzy_matches * 0.8 + semantic_matches * 0.6) / total_matches) * 10
        else:
            quality_bonus = 0
        
        score = base_score + preferred_bonus + quality_bonus
        
        # Build explanation
        positive_factors = []
        negative_factors = []
        suggestions = []
        
        if required_coverage >= 0.8:
            positive_factors.append(f"Strong coverage of required skills ({matched_required}/{total_required})")
        elif required_coverage >= 0.5:
            positive_factors.append(f"Moderate coverage of required skills ({matched_required}/{total_required})")
        else:
            negative_factors.append(f"Low coverage of required skills ({matched_required}/{total_required})")
        
        if exact_matches > 0:
            positive_factors.append(f"{exact_matches} exact skill matches")
        
        if missing_required:
            missing_names = [r.skill.normalized_name for r in missing_required[:5]]
            negative_factors.append(f"Missing required skills: {', '.join(missing_names)}")
            suggestions.append(f"Add these skills if you have them: {', '.join(missing_names)}")
        
        explanation = (
            f"Skill match score based on coverage of {total_required} required skills "
            f"and {total_preferred} preferred skills. "
            f"You matched {matched_required} required and {matched_preferred} preferred skills."
        )
        
        return ScoreBreakdown(
            score=round(score, 1),
            weight=self.weights['skill_match'],
            explanation=explanation,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            improvement_suggestions=suggestions,
        )
    
    def _calculate_experience_score(self, resume: ResumeData, job: JobDescriptionData) -> ScoreBreakdown:
        """
        Calculate experience alignment score.
        
        Factors:
        - Years of experience vs requirement
        - Seniority level alignment
        - Number of relevant positions
        
        Args:
            resume: Resume data
            job: Job description data
            
        Returns:
            ScoreBreakdown with explanation
        """
        score = 50.0  # Start at neutral
        positive_factors = []
        negative_factors = []
        suggestions = []
        
        # Check years of experience
        resume_years = resume.total_years_experience or 0
        min_required = job.min_years_experience or 0
        max_required = job.max_years_experience
        
        if min_required > 0:
            if resume_years >= min_required:
                # Meet or exceed minimum
                bonus = min(25, (resume_years - min_required + 1) * 5)
                score += bonus
                positive_factors.append(
                    f"Your experience ({resume_years:.1f} years) meets or exceeds "
                    f"the minimum requirement ({min_required} years)"
                )
            else:
                # Below minimum
                gap = min_required - resume_years
                penalty = min(30, gap * 10)
                score -= penalty
                negative_factors.append(
                    f"Experience gap: you have {resume_years:.1f} years, "
                    f"but {min_required} years required"
                )
                suggestions.append(
                    "Highlight transferable experience, personal projects, "
                    "or relevant coursework to bridge the experience gap"
                )
        else:
            # No specific requirement - neutral
            score += 10
        
        # Check for overqualification
        if max_required and resume_years > max_required * 1.5:
            score -= 10
            negative_factors.append(
                f"You may be overqualified ({resume_years:.1f} years vs "
                f"max {max_required} years requested)"
            )
        
        # Seniority alignment
        job_seniority = job.seniority
        if job_seniority != SeniorityLevel.UNKNOWN:
            seniority_years = {
                SeniorityLevel.ENTRY: 0,
                SeniorityLevel.JUNIOR: 1,
                SeniorityLevel.MID: 3,
                SeniorityLevel.SENIOR: 5,
                SeniorityLevel.LEAD: 7,
                SeniorityLevel.PRINCIPAL: 10,
                SeniorityLevel.EXECUTIVE: 15,
            }
            expected_years = seniority_years.get(job_seniority, 3)
            
            if abs(resume_years - expected_years) <= 2:
                score += 15
                positive_factors.append(
                    f"Experience level aligns with {job_seniority.value} role"
                )
        
        # Experience entries quality
        if resume.experience:
            if len(resume.experience) >= 2:
                score += 10
                positive_factors.append(
                    f"{len(resume.experience)} work experience entries provide good depth"
                )
        else:
            score -= 15
            negative_factors.append("No work experience detected in resume")
            suggestions.append(
                "Ensure your work experience is clearly formatted with company, title, dates, and descriptions"
            )
        
        score = max(0, min(100, score))
        
        explanation = (
            f"Experience score based on alignment with job requirements. "
            f"Job requires {min_required}-{max_required or '?'} years, "
            f"you have approximately {resume_years:.1f} years."
        )
        
        return ScoreBreakdown(
            score=round(score, 1),
            weight=self.weights['experience'],
            explanation=explanation,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            improvement_suggestions=suggestions,
        )
    
    def _calculate_keyword_score(self, skill_matches: dict, job: JobDescriptionData) -> ScoreBreakdown:
        """
        Calculate keyword coverage score.
        
        Different from skill score in that it considers:
        - All keywords (not just skills)
        - Frequency of mentions
        - Keyword placement
        
        Args:
            skill_matches: Results from skill matcher
            job: Job description data
            
        Returns:
            ScoreBreakdown with explanation
        """
        matched = skill_matches.get('matched_skills', [])
        missing_required = skill_matches.get('missing_required', [])
        
        # Calculate coverage
        total_keywords = len(job.required_skills) + len(job.preferred_skills)
        matched_count = len(matched)
        
        if total_keywords > 0:
            coverage = matched_count / total_keywords
        else:
            coverage = 1.0
        
        # Base score on coverage
        score = coverage * 80
        
        # Bonus for high-mention skills (repeated in resume)
        high_mention_skills = [
            m for m in matched 
            if m.resume_skill.mention_count >= 2
        ]
        if high_mention_skills:
            score += min(10, len(high_mention_skills) * 2)
        
        # Bonus for matching required skills specifically
        required_names = {r.skill.normalized_name for r in job.required_skills}
        matched_required = [
            m for m in matched
            if m.job_requirement and m.job_requirement.skill.normalized_name in required_names
        ]
        if matched_required:
            score += min(10, len(matched_required) * 1)
        
        score = max(0, min(100, score))
        
        positive_factors = []
        negative_factors = []
        suggestions = []
        
        if coverage >= 0.7:
            positive_factors.append(f"Good keyword coverage: {coverage*100:.0f}%")
        else:
            negative_factors.append(f"Low keyword coverage: {coverage*100:.0f}%")
        
        if high_mention_skills:
            positive_factors.append(
                f"{len(high_mention_skills)} skills mentioned multiple times (shows depth)"
            )
        
        if missing_required:
            missing_names = [r.skill.normalized_name for r in missing_required[:3]]
            suggestions.append(
                f"Include these keywords naturally in your experience: {', '.join(missing_names)}"
            )
        
        explanation = (
            f"Keyword coverage measures how many job keywords appear in your resume. "
            f"Found {matched_count} of {total_keywords} keywords ({coverage*100:.0f}% coverage)."
        )
        
        return ScoreBreakdown(
            score=round(score, 1),
            weight=self.weights['keyword_coverage'],
            explanation=explanation,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            improvement_suggestions=suggestions,
        )
    
    def _create_ats_score_breakdown(self, ats_analysis) -> ScoreBreakdown:
        """
        Create score breakdown from ATS analysis.
        
        Args:
            ats_analysis: ATSAnalysis from checker
            
        Returns:
            ScoreBreakdown with ATS details
        """
        high_issues = [i for i in ats_analysis.issues if i.severity == "high"]
        medium_issues = [i for i in ats_analysis.issues if i.severity == "medium"]
        
        positive_factors = []
        negative_factors = []
        suggestions = []
        
        if not high_issues:
            positive_factors.append("No critical ATS compatibility issues")
        else:
            for issue in high_issues:
                negative_factors.append(f"{issue.title}: {issue.description}")
                suggestions.append(issue.suggestion)
        
        for issue in medium_issues[:2]:  # Limit to avoid overwhelming
            negative_factors.append(issue.title)
        
        if ats_analysis.score >= 80:
            positive_factors.append("Good overall ATS compatibility")
        
        explanation = (
            f"ATS compatibility score: {ats_analysis.score:.0f}/100. "
            f"Found {len(high_issues)} high-severity and {len(medium_issues)} medium-severity issues."
        )
        
        return ScoreBreakdown(
            score=ats_analysis.score,
            weight=self.weights['ats'],
            explanation=explanation,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            improvement_suggestions=suggestions,
        )
    
    def _calculate_overall_score(
        self,
        skill_score: ScoreBreakdown,
        experience_score: ScoreBreakdown,
        keyword_score: ScoreBreakdown,
        ats_score: ScoreBreakdown
    ) -> float:
        """
        Calculate weighted overall score.
        
        Args:
            skill_score: Skill match breakdown
            experience_score: Experience alignment breakdown
            keyword_score: Keyword coverage breakdown
            ats_score: ATS compatibility breakdown
            
        Returns:
            Overall score 0-100
        """
        weighted_score = (
            skill_score.score * skill_score.weight +
            experience_score.score * experience_score.weight +
            keyword_score.score * keyword_score.weight +
            ats_score.score * ats_score.weight
        )
        
        return round(weighted_score, 1)
    
    def _calculate_grade(self, score: float) -> str:
        """
        Convert numeric score to letter grade.
        
        Args:
            score: Overall score 0-100
            
        Returns:
            Letter grade (A, B, C, D, F)
        """
        for grade, threshold in sorted(self.GRADE_THRESHOLDS.items(), key=lambda x: -x[1]):
            if score >= threshold:
                return grade
        return 'F'
    
    def _generate_improvement_suggestions(
        self,
        resume: ResumeData,
        job: JobDescriptionData,
        skill_matches: dict,
        ats_analysis
    ) -> tuple:
        """
        Generate prioritized improvement suggestions.
        
        Separates into quick wins (easy, high impact) and long-term improvements.
        
        Returns:
            Tuple of (quick_wins, long_term_improvements)
        """
        quick_wins = []
        long_term = []
        
        missing_required = skill_matches.get('missing_required', [])
        
        # Quick wins: Add missing skills you might have
        if missing_required:
            skill_names = [r.skill.normalized_name for r in missing_required[:3]]
            quick_wins.append(ImprovementSuggestion(
                category="skill",
                priority="high",
                title="Add Missing Required Skills",
                description=f"These skills are required but not found in your resume: {', '.join(skill_names)}",
                example=f"Add to your skills section: {', '.join(skill_names)}",
                affected_section="skills"
            ))
        
        # Quick win: Add keywords to experience
        if missing_required and resume.experience:
            quick_wins.append(ImprovementSuggestion(
                category="keyword",
                priority="high",
                title="Incorporate Keywords in Experience",
                description="Add missing keywords naturally into your job descriptions",
                example="Instead of 'Built web applications', try 'Built React-based web applications using TypeScript'",
                affected_section="experience"
            ))
        
        # ATS-related quick wins
        for issue in ats_analysis.issues[:2]:
            if issue.severity == "high":
                quick_wins.append(ImprovementSuggestion(
                    category="formatting",
                    priority="high",
                    title=issue.title,
                    description=issue.description,
                    example=issue.example if issue.example else "",
                    affected_section=""
                ))
        
        # Long-term: Experience building
        if resume.total_years_experience and job.min_years_experience:
            if resume.total_years_experience < job.min_years_experience:
                long_term.append(ImprovementSuggestion(
                    category="experience",
                    priority="medium",
                    title="Gain More Experience",
                    description=f"This role requires {job.min_years_experience} years of experience",
                    example="Consider freelance projects, open source contributions, or personal projects to build experience",
                    affected_section=""
                ))
        
        # Long-term: Certifications
        if job.required_skills:
            tech_skills = [r.skill.normalized_name for r in job.required_skills[:3]]
            long_term.append(ImprovementSuggestion(
                category="certification",
                priority="low",
                title="Consider Relevant Certifications",
                description="Certifications can strengthen your candidacy",
                example=f"Look for certifications in: {', '.join(tech_skills)}",
                affected_section="certifications"
            ))
        
        return quick_wins, long_term
    
    def _generate_bullet_examples(
        self,
        resume: ResumeData,
        job: JobDescriptionData,
        skill_matches: dict
    ) -> list:
        """
        Generate example bullet point rewrites that incorporate missing keywords.
        
        Returns:
            List of example strings
        """
        examples = []
        
        missing = skill_matches.get('missing_required', [])
        if not missing:
            return examples
        
        # Generate generic examples for top missing skills
        for req in missing[:3]:
            skill_name = req.skill.normalized_name
            
            examples.append({
                "skill": skill_name,
                "before": f"Developed web applications for the team",
                "after": f"Developed web applications using {skill_name}, improving team productivity by 20%",
                "explanation": f"Added '{skill_name}' with quantified impact"
            })
        
        return examples
    
    def _generate_placement_suggestions(
        self,
        skill_matches: dict,
        resume: ResumeData
    ) -> list:
        """
        Generate suggestions for where to place missing skills.
        
        Returns:
            List of placement suggestion strings
        """
        suggestions = []
        
        missing = skill_matches.get('missing_required', [])
        if not missing:
            return suggestions
        
        # Skills section
        skill_names = [r.skill.normalized_name for r in missing[:5]]
        suggestions.append(
            f"Skills Section: Add these skills if you have them - {', '.join(skill_names)}"
        )
        
        # Experience section
        suggestions.append(
            "Experience Section: Incorporate 2-3 of these skills into your bullet points "
            "with specific examples of how you used them"
        )
        
        # Projects section
        if 'projects' in resume.sections_detected:
            suggestions.append(
                "Projects Section: Highlight projects where you used or learned these technologies"
            )
        
        return suggestions


# Convenience function
def calculate_match(resume: ResumeData, job: JobDescriptionData) -> MatchResult:
    """
    Calculate match between resume and job description.
    
    Args:
        resume: Parsed resume data
        job: Parsed job description data
        
    Returns:
        MatchResult with all scores and suggestions
    """
    scorer = MatchScorer()
    return scorer.calculate_match(resume, job)
