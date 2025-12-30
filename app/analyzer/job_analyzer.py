"""
Job Description Analyzer

This module parses and analyzes job descriptions to extract:
- Required vs preferred skills
- Experience requirements
- Seniority level signals
- Implicit expectations (fast-paced, ownership, etc.)
- Education requirements

The analyzer uses rule-based heuristics for deterministic, reproducible results.
"""

import re
from typing import Optional, Tuple
from dataclasses import dataclass

from ..models import (
    JobDescriptionData, JobRequirement, Skill, 
    RequirementLevel, SeniorityLevel, SkillCategory
)
from ..knowledge_base import (
    normalize_skill, get_skill_category, detect_seniority,
    SENIORITY_INDICATORS, IMPLICIT_EXPECTATIONS,
    SKILL_SYNONYMS, ALIAS_TO_CANONICAL, DEGREE_LEVELS
)


class JobDescriptionAnalyzer:
    """
    Analyzes job descriptions to extract structured requirements.
    
    The analyzer processes raw job description text and produces
    a structured JobDescriptionData object containing:
    - Skills (required and preferred)
    - Experience requirements
    - Education requirements
    - Seniority level
    - Implicit expectations
    
    Usage:
        analyzer = JobDescriptionAnalyzer()
        result = analyzer.analyze(job_text)
    """
    
    def __init__(self):
        """Initialize the analyzer."""
        # Build skill pattern for extraction
        self._skill_pattern = self._build_skill_pattern()
        
        # Patterns that indicate required vs preferred
        self._required_patterns = [
            r'\brequired?\b',
            r'\bmust have\b',
            r'\bmust be\b',
            r'\bessential\b',
            r'\bmandatory\b',
            r'\bminimum\b',
            r'\bneed[s]?\b',
            r'\brequirements?\b',
        ]
        
        self._preferred_patterns = [
            r'\bpreferred\b',
            r'\bnice to have\b',
            r'\bplus\b',
            r'\bbonus\b',
            r'\bdesirable\b',
            r'\badvantage\b',
            r'\bbeneficial\b',
            r'\bideally\b',
            r'\bfamiliar(?:ity)?\b',
            r'\bexposure\b',
        ]
        
        # Experience pattern
        self._experience_patterns = [
            r'(\d+)\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
            r'(\d+)\s*(?:to|-)\s*(\d+)\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)',
            r'at\s+least\s+(\d+)\s*(?:years?|yrs?)',
            r'minimum\s+(?:of\s+)?(\d+)\s*(?:years?|yrs?)',
        ]
    
    def analyze(self, job_text: str) -> JobDescriptionData:
        """
        Analyze a job description and extract structured data.
        
        Args:
            job_text: Raw job description text
            
        Returns:
            JobDescriptionData object with extracted information
        """
        result = JobDescriptionData(raw_text=job_text)
        
        # Detect job title (usually first meaningful line)
        result.title = self._extract_job_title(job_text)
        
        # Detect seniority level
        result.seniority = self._detect_seniority(job_text)
        
        # Extract experience requirements
        min_exp, max_exp = self._extract_experience_requirements(job_text)
        result.min_years_experience = min_exp
        result.max_years_experience = max_exp
        
        # Extract skills (required and preferred)
        required_skills, preferred_skills = self._extract_skills(job_text)
        result.required_skills = required_skills
        result.preferred_skills = preferred_skills
        
        # Extract education requirements
        result.degree_required, result.degree_preferred = self._extract_education_requirements(job_text)
        
        # Detect implicit expectations
        result.implicit_expectations = self._extract_implicit_expectations(job_text)
        
        # Detect culture signals
        result.culture_signals = self._extract_culture_signals(job_text)
        
        return result
    
    def _build_skill_pattern(self) -> re.Pattern:
        """Build regex pattern to match known skills."""
        all_skill_terms = set()
        for canonical, aliases in SKILL_SYNONYMS.items():
            all_skill_terms.add(canonical)
            all_skill_terms.update(aliases)
        
        sorted_terms = sorted(all_skill_terms, key=len, reverse=True)
        escaped_terms = [re.escape(term) for term in sorted_terms]
        pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'
        
        return re.compile(pattern, re.IGNORECASE)
    
    def _extract_job_title(self, text: str) -> str:
        """
        Extract job title from the beginning of the job description.
        
        The title is usually the first non-empty line or appears near the top.
        
        Args:
            text: Job description text
            
        Returns:
            Extracted job title or empty string
        """
        lines = text.strip().split('\n')
        
        # Common patterns for job titles
        title_patterns = [
            r'^(?:job\s+)?title\s*[:;]\s*(.+)$',
            r'^(?:position|role)\s*[:;]\s*(.+)$',
        ]
        
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if not line:
                continue
            
            # Check for explicit title label
            for pattern in title_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()[:200]
            
            # If line looks like a job title (short, contains job keywords)
            if len(line) < 100 and self._looks_like_job_title(line):
                return line
        
        # Fall back to first meaningful line
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 100:
                return line
        
        return ""
    
    def _looks_like_job_title(self, text: str) -> bool:
        """
        Check if text appears to be a job title.
        
        Args:
            text: Text to check
            
        Returns:
            True if text looks like a job title
        """
        title_keywords = [
            'engineer', 'developer', 'manager', 'director', 'analyst',
            'architect', 'consultant', 'lead', 'specialist', 'coordinator',
            'administrator', 'designer', 'scientist', 'researcher'
        ]
        
        text_lower = text.lower()
        
        # Check if contains common job title words
        return any(keyword in text_lower for keyword in title_keywords)
    
    def _detect_seniority(self, text: str) -> SeniorityLevel:
        """
        Detect seniority level from job description.
        
        Uses indicators from the knowledge base.
        
        Args:
            text: Job description text
            
        Returns:
            SeniorityLevel enum value
        """
        level_str = detect_seniority(text)
        
        level_mapping = {
            'entry': SeniorityLevel.ENTRY,
            'junior': SeniorityLevel.JUNIOR,
            'mid': SeniorityLevel.MID,
            'senior': SeniorityLevel.SENIOR,
            'lead': SeniorityLevel.LEAD,
            'principal': SeniorityLevel.PRINCIPAL,
            'executive': SeniorityLevel.EXECUTIVE,
            'unknown': SeniorityLevel.UNKNOWN,
        }
        
        return level_mapping.get(level_str, SeniorityLevel.UNKNOWN)
    
    def _extract_experience_requirements(self, text: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Extract minimum and maximum years of experience required.
        
        Args:
            text: Job description text
            
        Returns:
            Tuple of (min_years, max_years), either can be None
        """
        text_lower = text.lower()
        min_years = None
        max_years = None
        
        for pattern in self._experience_patterns:
            for match in re.finditer(pattern, text_lower):
                groups = match.groups()
                
                if len(groups) == 2 and groups[1]:
                    # Range pattern like "3-5 years"
                    try:
                        min_val = float(groups[0])
                        max_val = float(groups[1])
                        if min_years is None or min_val < min_years:
                            min_years = min_val
                        if max_years is None or max_val > max_years:
                            max_years = max_val
                    except ValueError:
                        pass
                elif groups[0]:
                    # Single value pattern
                    try:
                        years = float(groups[0])
                        if min_years is None or years < min_years:
                            min_years = years
                    except ValueError:
                        pass
        
        return min_years, max_years
    
    def _extract_skills(self, text: str) -> Tuple[list, list]:
        """
        Extract skills from job description, categorized as required or preferred.
        
        The algorithm:
        1. Find all skill mentions in the text
        2. Determine context around each mention
        3. Classify as required or preferred based on context
        4. Weight by number of mentions
        
        Args:
            text: Job description text
            
        Returns:
            Tuple of (required_skills, preferred_skills) as JobRequirement lists
        """
        # First, identify sections that are clearly required vs preferred
        required_section = ""
        preferred_section = ""
        
        # Look for section headers
        lines = text.split('\n')
        current_section = "required"  # Default assumption
        
        section_content = {"required": [], "preferred": []}
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check for section indicators
            if any(p in line_lower for p in ['preferred', 'nice to have', 'bonus', 'plus']):
                current_section = "preferred"
            elif any(p in line_lower for p in ['required', 'must have', 'requirements', 'minimum', 'essential']):
                current_section = "required"
            
            section_content[current_section].append(line)
        
        required_text = '\n'.join(section_content["required"])
        preferred_text = '\n'.join(section_content["preferred"])
        
        # Extract skills from each section
        required_skills = self._extract_skills_from_text(required_text, RequirementLevel.REQUIRED)
        preferred_skills = self._extract_skills_from_text(preferred_text, RequirementLevel.PREFERRED)
        
        # Remove duplicates (prefer required classification)
        required_names = {s.skill.normalized_name for s in required_skills}
        preferred_skills = [s for s in preferred_skills if s.skill.normalized_name not in required_names]
        
        return required_skills, preferred_skills
    
    def _extract_skills_from_text(self, text: str, default_level: RequirementLevel) -> list:
        """
        Extract skills from a section of text.
        
        Args:
            text: Text to extract skills from
            default_level: Default requirement level for found skills
            
        Returns:
            List of JobRequirement objects
        """
        skills_dict = {}
        
        for match in self._skill_pattern.finditer(text):
            skill_text = match.group(1)
            normalized = normalize_skill(skill_text)
            
            # Get context around the match
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end]
            
            # Check if context indicates preferred vs required
            level = default_level
            context_lower = context.lower()
            
            if any(re.search(p, context_lower) for p in self._preferred_patterns):
                level = RequirementLevel.PREFERRED
            elif any(re.search(p, context_lower) for p in self._required_patterns):
                level = RequirementLevel.REQUIRED
            
            # Extract years required if mentioned
            years_required = None
            years_match = re.search(r'(\d+)\+?\s*(?:years?|yrs?)', context_lower)
            if years_match:
                years_required = float(years_match.group(1))
            
            if normalized not in skills_dict:
                skill = Skill(
                    name=skill_text,
                    normalized_name=normalized,
                    category=self._get_skill_category_enum(normalized),
                    context=context[:100]
                )
                skills_dict[normalized] = JobRequirement(
                    skill=skill,
                    level=level,
                    years_required=years_required,
                    context=context
                )
            else:
                # Update with more restrictive level if needed
                if level == RequirementLevel.REQUIRED:
                    skills_dict[normalized].level = level
                skills_dict[normalized].skill.mention_count += 1
        
        return list(skills_dict.values())
    
    def _get_skill_category_enum(self, skill_name: str) -> SkillCategory:
        """Map skill category string to SkillCategory enum."""
        category_str = get_skill_category(skill_name)
        
        category_mapping = {
            'programming_language': SkillCategory.HARD,
            'frontend_framework': SkillCategory.TOOL,
            'backend_framework': SkillCategory.TOOL,
            'database': SkillCategory.TOOL,
            'cloud': SkillCategory.TOOL,
            'devops': SkillCategory.TOOL,
            'soft_skill': SkillCategory.SOFT,
            'methodology': SkillCategory.SOFT,
        }
        
        return category_mapping.get(category_str, SkillCategory.HARD)
    
    def _extract_education_requirements(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract education requirements from job description.
        
        Args:
            text: Job description text
            
        Returns:
            Tuple of (required_degree, preferred_degree)
        """
        text_lower = text.lower()
        
        required_degree = None
        preferred_degree = None
        
        # Check each degree level
        for degree_level, keywords in DEGREE_LEVELS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    # Check if this is required or preferred
                    # Look at nearby context
                    idx = text_lower.find(keyword)
                    context = text_lower[max(0, idx-50):min(len(text_lower), idx+50)]
                    
                    if 'prefer' in context or 'nice to have' in context:
                        if preferred_degree is None:
                            preferred_degree = degree_level
                    else:
                        # Default to required if degree is mentioned
                        if required_degree is None:
                            required_degree = degree_level
        
        return required_degree, preferred_degree
    
    def _extract_implicit_expectations(self, text: str) -> list:
        """
        Extract implicit expectations from job description.
        
        These are expectations that aren't explicitly listed as requirements
        but are implied by the language used.
        
        Args:
            text: Job description text
            
        Returns:
            List of expectation strings
        """
        text_lower = text.lower()
        expectations = []
        
        for expectation_name, indicators in IMPLICIT_EXPECTATIONS.items():
            for indicator in indicators:
                if indicator in text_lower:
                    expectations.append(expectation_name)
                    break  # Only add once per category
        
        return expectations
    
    def _extract_culture_signals(self, text: str) -> list:
        """
        Extract company culture signals from job description.
        
        Args:
            text: Job description text
            
        Returns:
            List of culture signal strings
        """
        signals = []
        text_lower = text.lower()
        
        culture_indicators = {
            "startup": ["startup", "early stage", "series a", "series b", "fast-growing"],
            "enterprise": ["enterprise", "fortune 500", "large scale", "established"],
            "remote_friendly": ["remote", "work from home", "distributed team", "anywhere"],
            "diversity_focused": ["diverse", "diversity", "inclusion", "belonging", "dei"],
            "learning_focused": ["learning", "growth", "development opportunities", "training"],
            "work_life_balance": ["work-life balance", "flexible", "wellness", "mental health"],
        }
        
        for signal_name, indicators in culture_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    signals.append(signal_name)
                    break
        
        return signals


# Convenience function
def analyze_job_description(job_text: str) -> JobDescriptionData:
    """
    Analyze a job description and return structured data.
    
    Args:
        job_text: Raw job description text
        
    Returns:
        JobDescriptionData object with extracted information
    """
    analyzer = JobDescriptionAnalyzer()
    return analyzer.analyze(job_text)
