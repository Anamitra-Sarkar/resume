"""
Skill Matching Engine

This module provides fuzzy and semantic matching between resume skills
and job requirements. It uses multiple strategies:

1. Exact matching (canonical name comparison)
2. Fuzzy matching (edit distance for typos/variations)
3. Semantic matching (related skills in same domain)

All matching is deterministic and reproducible.
"""

from typing import Optional, Tuple

try:
    from rapidfuzz import fuzz
except ImportError:
    fuzz = None

from ..models import Skill, SkillMatch, JobRequirement
from ..knowledge_base import normalize_skill, find_semantic_matches


class SkillMatcher:
    """
    Matches resume skills against job requirements.
    
    Uses a multi-tier matching approach:
    1. Exact match (normalized names are identical)
    2. Fuzzy match (similar names, handles typos)
    3. Semantic match (related skills in same domain)
    
    Each match includes a confidence score and explanation.
    """
    
    # Threshold for fuzzy matching (0-100 scale from rapidfuzz)
    FUZZY_THRESHOLD = 85
    
    # Threshold for semantic matching confidence
    SEMANTIC_THRESHOLD = 0.6
    
    def __init__(self):
        """Initialize the skill matcher."""
        pass
    
    def match_skill(
        self, 
        resume_skill: Skill, 
        job_requirements: list
    ) -> Optional[SkillMatch]:
        """
        Find the best match for a resume skill in job requirements.
        
        Args:
            resume_skill: Skill from the resume
            job_requirements: List of JobRequirement from job description
            
        Returns:
            SkillMatch object if a match is found, None otherwise
        """
        # Try matching strategies in order of confidence
        
        # 1. Exact match
        for req in job_requirements:
            if self._is_exact_match(resume_skill, req.skill):
                return SkillMatch(
                    resume_skill=resume_skill,
                    job_requirement=req,
                    match_type="exact",
                    match_score=1.0,
                    explanation=f"'{resume_skill.normalized_name}' exactly matches "
                                f"required skill '{req.skill.normalized_name}'"
                )
        
        # 2. Fuzzy match
        best_fuzzy = self._find_best_fuzzy_match(resume_skill, job_requirements)
        if best_fuzzy:
            return best_fuzzy
        
        # 3. Semantic match
        best_semantic = self._find_best_semantic_match(resume_skill, job_requirements)
        if best_semantic:
            return best_semantic
        
        # No match found
        return None
    
    def _is_exact_match(self, skill1: Skill, skill2: Skill) -> bool:
        """
        Check if two skills are exact matches.
        
        Comparison is done on normalized names (case-insensitive,
        aliases resolved to canonical form).
        
        Args:
            skill1: First skill
            skill2: Second skill
            
        Returns:
            True if skills match exactly
        """
        return skill1.normalized_name.lower() == skill2.normalized_name.lower()
    
    def _find_best_fuzzy_match(
        self, 
        resume_skill: Skill, 
        job_requirements: list
    ) -> Optional[SkillMatch]:
        """
        Find the best fuzzy match for a skill.
        
        Uses edit distance to handle typos and minor variations.
        
        Args:
            resume_skill: Skill to match
            job_requirements: Requirements to match against
            
        Returns:
            SkillMatch if a good fuzzy match exists, None otherwise
        """
        if fuzz is None:
            # Fuzzy matching not available without rapidfuzz
            return None
        
        best_match = None
        best_score = 0
        
        resume_name = resume_skill.normalized_name.lower()
        
        for req in job_requirements:
            req_name = req.skill.normalized_name.lower()
            
            # Calculate similarity score
            # Using token_sort_ratio to handle word order differences
            score = fuzz.token_sort_ratio(resume_name, req_name)
            
            if score >= self.FUZZY_THRESHOLD and score > best_score:
                best_score = score
                best_match = req
        
        if best_match:
            # Convert rapidfuzz score (0-100) to our scale (0-1)
            normalized_score = best_score / 100.0
            
            return SkillMatch(
                resume_skill=resume_skill,
                job_requirement=best_match,
                match_type="fuzzy",
                match_score=normalized_score * 0.9,  # Slightly lower than exact
                explanation=f"'{resume_skill.normalized_name}' closely matches "
                            f"'{best_match.skill.normalized_name}' "
                            f"(similarity: {best_score}%)"
            )
        
        return None
    
    def _find_best_semantic_match(
        self, 
        resume_skill: Skill, 
        job_requirements: list
    ) -> Optional[SkillMatch]:
        """
        Find a semantic match (related skill in same domain).
        
        For example, if job wants React but resume has Vue.js,
        this is a partial match (both are frontend frameworks).
        
        Args:
            resume_skill: Skill to match
            job_requirements: Requirements to match against
            
        Returns:
            SkillMatch if a semantic match exists, None otherwise
        """
        # Get skills related to the resume skill
        related_skills = find_semantic_matches(resume_skill.normalized_name)
        
        if not related_skills:
            return None
        
        related_set = {s.lower() for s in related_skills}
        
        for req in job_requirements:
            if req.skill.normalized_name.lower() in related_set:
                return SkillMatch(
                    resume_skill=resume_skill,
                    job_requirement=req,
                    match_type="semantic",
                    match_score=self.SEMANTIC_THRESHOLD,
                    explanation=f"'{resume_skill.normalized_name}' is related to "
                                f"required skill '{req.skill.normalized_name}' "
                                f"(both are in the same technology domain)"
                )
        
        return None
    
    def match_all_skills(
        self, 
        resume_skills: list, 
        required_skills: list,
        preferred_skills: list
    ) -> dict:
        """
        Match all resume skills against job requirements.
        
        Returns a comprehensive breakdown of matches, misses, and irrelevant skills.
        
        Args:
            resume_skills: List of Skill from resume
            required_skills: List of JobRequirement (required)
            preferred_skills: List of JobRequirement (preferred)
            
        Returns:
            Dictionary with match results:
            - matched_skills: Skills that match requirements
            - missing_required: Required skills not in resume
            - missing_preferred: Preferred skills not in resume
            - irrelevant_skills: Resume skills not matching any requirement
        """
        all_requirements = required_skills + preferred_skills
        
        matched_skills = []
        matched_requirement_names = set()
        matched_resume_names = set()
        
        # Try to match each resume skill
        for skill in resume_skills:
            match = self.match_skill(skill, all_requirements)
            if match:
                matched_skills.append(match)
                if match.job_requirement:
                    matched_requirement_names.add(match.job_requirement.skill.normalized_name)
                matched_resume_names.add(skill.normalized_name)
        
        # Find missing required skills
        missing_required = [
            req for req in required_skills
            if req.skill.normalized_name not in matched_requirement_names
        ]
        
        # Find missing preferred skills
        missing_preferred = [
            req for req in preferred_skills
            if req.skill.normalized_name not in matched_requirement_names
        ]
        
        # Find irrelevant resume skills (not matching any requirement)
        irrelevant_skills = [
            skill for skill in resume_skills
            if skill.normalized_name not in matched_resume_names
        ]
        
        return {
            "matched_skills": matched_skills,
            "missing_required": missing_required,
            "missing_preferred": missing_preferred,
            "irrelevant_skills": irrelevant_skills,
        }


# Module-level convenience instance
_matcher = None

def get_matcher() -> SkillMatcher:
    """Get or create the skill matcher singleton."""
    global _matcher
    if _matcher is None:
        _matcher = SkillMatcher()
    return _matcher
