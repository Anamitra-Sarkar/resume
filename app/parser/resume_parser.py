"""
Resume Parser - Main Module

This module coordinates the parsing of resume files in various formats
and extracts structured data including skills, experience, education, etc.

The parser is designed to:
1. Handle multiple file formats (PDF, DOCX, TXT)
2. Extract structured information from unstructured text
3. Detect resume sections and their content
4. Identify skills with context and estimated experience
5. Provide quality indicators for ATS compatibility
"""

import re
from typing import Optional, Tuple, Union
from pathlib import Path

from ..models import (
    ResumeData, Skill, Education, WorkExperience, 
    Certification, SkillCategory
)
from ..knowledge_base import (
    normalize_skill, get_skill_category, SECTION_HEADERS,
    SKILL_SYNONYMS, ALIAS_TO_CANONICAL
)
from .pdf_parser import extract_text_from_pdf, has_tables as pdf_has_tables, has_images
from .docx_parser import extract_text_from_docx, has_tables as docx_has_tables
from .txt_parser import extract_text_from_txt


class ResumeParser:
    """
    Main resume parser class.
    
    Handles parsing of resume files and extraction of structured data.
    All processing is done in-memory with no persistent storage.
    
    Usage:
        parser = ResumeParser()
        result = parser.parse_file(file_content, "resume.pdf")
        # or
        result = parser.parse_text(resume_text)
    """
    
    def __init__(self):
        """Initialize the resume parser."""
        # Build skill patterns for extraction
        self._skill_pattern = self._build_skill_pattern()
        
        # Common date patterns for experience parsing
        self._date_patterns = [
            r'(\w+\s+\d{4})\s*[-–—to]+\s*(\w+\s+\d{4}|[Pp]resent|[Cc]urrent)',
            r'(\d{1,2}/\d{4})\s*[-–—to]+\s*(\d{1,2}/\d{4}|[Pp]resent|[Cc]urrent)',
            r'(\d{4})\s*[-–—to]+\s*(\d{4}|[Pp]resent|[Cc]urrent)',
        ]
    
    def parse_file(self, file_content: bytes, filename: str) -> ResumeData:
        """
        Parse a resume file and extract structured data.
        
        Args:
            file_content: Raw bytes of the file
            filename: Original filename (used to determine file type)
            
        Returns:
            ResumeData object with extracted information
            
        Raises:
            ValueError: If file type is not supported
        """
        # Determine file type and extract text
        ext = Path(filename).suffix.lower()
        
        if ext == '.pdf':
            text = extract_text_from_pdf(file_content)
            has_tables = pdf_has_tables(file_content)
            has_graphics = has_images(file_content)
        elif ext == '.docx':
            text = extract_text_from_docx(file_content)
            has_tables = docx_has_tables(file_content)
            has_graphics = False  # Not easily detected in DOCX
        elif ext == '.txt':
            text = extract_text_from_txt(file_content)
            has_tables = False
            has_graphics = False
        else:
            raise ValueError(
                f"Unsupported file type: {ext}. "
                "Supported types: .pdf, .docx, .txt"
            )
        
        # Parse the extracted text
        result = self.parse_text(text)
        
        # Add format-specific analysis
        if has_tables:
            result.has_clear_headings = True  # Tables often indicate structured content
        
        return result
    
    def parse_text(self, text: str) -> ResumeData:
        """
        Parse resume text and extract structured data.
        
        This is the main parsing logic that works on text content
        regardless of the original file format.
        
        Args:
            text: Resume content as plain text
            
        Returns:
            ResumeData object with extracted information
        """
        result = ResumeData(raw_text=text)
        
        # Detect contact information (existence only, not stored)
        result.has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text))
        result.has_phone = bool(re.search(r'[\+]?[\d\s\-\(\)]{10,}', text))
        result.has_linkedin = bool(re.search(r'linkedin\.com|linkedin', text, re.I))
        result.has_github = bool(re.search(r'github\.com|github', text, re.I))
        
        # Detect sections
        sections = self._detect_sections(text)
        result.sections_detected = list(sections.keys())
        result.section_order = self._get_section_order(text, sections)
        
        # Extract skills
        result.skills = self._extract_skills(text, sections.get('skills', ''))
        
        # Extract education
        result.education = self._extract_education(sections.get('education', text))
        
        # Extract work experience
        result.experience = self._extract_experience(sections.get('experience', text))
        
        # Extract certifications
        result.certifications = self._extract_certifications(
            sections.get('certifications', text)
        )
        
        # Extract summary if present
        result.summary = sections.get('summary', '')[:500]  # Limit length
        
        # Calculate total years of experience
        result.total_years_experience = self._calculate_total_experience(result.experience)
        
        # Assess formatting quality
        result.has_clear_headings = len(result.sections_detected) >= 2
        result.has_bullet_points = bool(re.search(r'^[\s]*[•\-\*\>]\s', text, re.MULTILINE))
        result.estimated_ats_friendliness = self._estimate_ats_friendliness(result, text)
        
        return result
    
    def _build_skill_pattern(self) -> re.Pattern:
        """
        Build a regex pattern to match known skills.
        
        Creates a pattern from the knowledge base that can find skills
        in resume text, including their aliases.
        """
        # Get all skill names and their aliases
        all_skill_terms = set()
        for canonical, aliases in SKILL_SYNONYMS.items():
            all_skill_terms.add(canonical)
            all_skill_terms.update(aliases)
        
        # Sort by length (longest first) to match longer terms first
        sorted_terms = sorted(all_skill_terms, key=len, reverse=True)
        
        # Escape special regex characters and create pattern
        escaped_terms = [re.escape(term) for term in sorted_terms]
        pattern = r'\b(' + '|'.join(escaped_terms) + r')\b'
        
        return re.compile(pattern, re.IGNORECASE)
    
    def _detect_sections(self, text: str) -> dict:
        """
        Detect and extract resume sections.
        
        Uses heuristics to find section headers and extract their content.
        
        Args:
            text: Resume text
            
        Returns:
            Dictionary mapping section names to their content
        """
        sections = {}
        lines = text.split('\n')
        
        # Find potential section headers
        section_starts = []
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            
            for section_name, headers in SECTION_HEADERS.items():
                for header in headers:
                    # Check if line is primarily a section header
                    if self._is_section_header(line_lower, header):
                        section_starts.append((i, section_name))
                        break
        
        # Extract content for each section
        for idx, (start_line, section_name) in enumerate(section_starts):
            # Find end of section (start of next section or end of document)
            if idx + 1 < len(section_starts):
                end_line = section_starts[idx + 1][0]
            else:
                end_line = len(lines)
            
            # Extract section content (excluding header line)
            section_content = '\n'.join(lines[start_line + 1:end_line]).strip()
            
            # Store if we haven't seen this section yet
            if section_name not in sections or len(section_content) > len(sections[section_name]):
                sections[section_name] = section_content
        
        return sections
    
    def _is_section_header(self, line: str, header: str) -> bool:
        """
        Determine if a line is likely a section header.
        
        Section headers are typically:
        - Short (usually less than 50 chars)
        - Stand alone on a line
        - May be in all caps or title case
        
        Args:
            line: Line to check (lowercase, stripped)
            header: Header pattern to match
            
        Returns:
            True if the line appears to be this section header
        """
        if not line:
            return False
        
        # Line should contain the header
        if header not in line:
            return False
        
        # Line should be relatively short (section headers are concise)
        if len(line) > 50:
            return False
        
        # Header should be a significant portion of the line
        if len(header) / len(line) < 0.5:
            return False
        
        return True
    
    def _get_section_order(self, text: str, sections: dict) -> list:
        """
        Determine the order in which sections appear.
        
        This is useful for ATS analysis (some orderings are preferred).
        
        Args:
            text: Resume text
            sections: Detected sections
            
        Returns:
            List of section names in order of appearance
        """
        positions = []
        text_lower = text.lower()
        
        for section_name in sections.keys():
            # Find first occurrence of any header for this section
            for header in SECTION_HEADERS.get(section_name, []):
                pos = text_lower.find(header)
                if pos != -1:
                    positions.append((pos, section_name))
                    break
        
        # Sort by position and return section names
        positions.sort()
        return [name for _, name in positions]
    
    def _extract_skills(self, full_text: str, skills_section: str) -> list:
        """
        Extract skills from resume text.
        
        Uses multiple strategies:
        1. Pattern matching against known skills
        2. Skills section parsing (if detected)
        3. Context-aware skill detection
        
        Args:
            full_text: Complete resume text
            skills_section: Text from skills section (if found)
            
        Returns:
            List of Skill objects
        """
        skills_dict = {}  # canonical_name -> Skill object
        
        # Strategy 1: Pattern matching in full text
        for match in self._skill_pattern.finditer(full_text):
            skill_text = match.group(1)
            normalized = normalize_skill(skill_text)
            
            if normalized not in skills_dict:
                skills_dict[normalized] = Skill(
                    name=skill_text,
                    normalized_name=normalized,
                    category=self._get_skill_category_enum(normalized),
                    mention_count=1
                )
            else:
                skills_dict[normalized].mention_count += 1
        
        # Strategy 2: Parse skills section for additional skills
        if skills_section:
            # Skills sections often use comma, pipe, or newline separation
            skill_candidates = re.split(r'[,|\n•\-\*]', skills_section)
            
            for candidate in skill_candidates:
                candidate = candidate.strip()
                
                # Skip if too short or too long
                if len(candidate) < 2 or len(candidate) > 50:
                    continue
                
                # Skip if it's just whitespace or common non-skill words
                if not candidate or candidate.lower() in ['and', 'or', 'etc', 'skills']:
                    continue
                
                normalized = normalize_skill(candidate)
                
                if normalized not in skills_dict:
                    # This might be a skill not in our knowledge base
                    skills_dict[normalized] = Skill(
                        name=candidate,
                        normalized_name=normalized,
                        category=self._get_skill_category_enum(normalized),
                        mention_count=1,
                        context="skills_section"
                    )
        
        return list(skills_dict.values())
    
    def _get_skill_category_enum(self, skill_name: str) -> SkillCategory:
        """
        Map skill category string to SkillCategory enum.
        
        Args:
            skill_name: Canonical skill name
            
        Returns:
            SkillCategory enum value
        """
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
    
    def _extract_education(self, education_text: str) -> list:
        """
        Extract education entries from text.
        
        Looks for:
        - Degree names (BS, MS, PhD, etc.)
        - Field of study
        - Institution names
        - Graduation years
        
        Args:
            education_text: Text from education section or full resume
            
        Returns:
            List of Education objects
        """
        education_list = []
        
        # Common degree patterns
        degree_patterns = [
            # "Bachelor of Science in Computer Science"
            r"(Bachelor|Master|Doctor|Associate|PhD|Ph\.D|B\.S|M\.S|B\.A|M\.A|MBA|B\.Sc|M\.Sc)\.?\s+(?:of\s+)?([\w\s]+?)(?:\s+in\s+([\w\s]+))?",
            # "BS in Computer Science"
            r"\b(BS|MS|BA|MA|PhD|B\.S\.|M\.S\.|B\.A\.|M\.A\.|MBA)\b\.?\s+(?:in\s+)?([\w\s]+)",
        ]
        
        # Year patterns
        year_pattern = r'\b(19|20)\d{2}\b'
        
        for pattern in degree_patterns:
            for match in re.finditer(pattern, education_text, re.IGNORECASE):
                degree_type = match.group(1)
                
                # Try to extract additional info
                field = match.group(2) if len(match.groups()) > 1 else ""
                if field:
                    field = field.strip()
                
                # Find nearby year
                match_start = match.start()
                nearby_text = education_text[max(0, match_start-50):match_start+100]
                year_match = re.search(year_pattern, nearby_text)
                year = int(year_match.group()) if year_match else None
                
                education_list.append(Education(
                    degree=degree_type,
                    field_of_study=field,
                    graduation_year=year
                ))
        
        return education_list
    
    def _extract_experience(self, experience_text: str) -> list:
        """
        Extract work experience entries from text.
        
        Looks for:
        - Job titles
        - Company names
        - Date ranges
        - Descriptions/achievements
        
        Args:
            experience_text: Text from experience section or full resume
            
        Returns:
            List of WorkExperience objects
        """
        experiences = []
        
        # Split into potential entries based on date patterns or clear separations
        # This is a heuristic approach
        lines = experience_text.split('\n')
        
        current_experience = None
        description_buffer = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line contains a date range (new entry)
            has_date = False
            for pattern in self._date_patterns:
                if re.search(pattern, line):
                    has_date = True
                    break
            
            # Also check for job title patterns
            is_likely_title = self._is_likely_job_title(line)
            
            if has_date or (is_likely_title and current_experience is not None):
                # Save previous experience if exists
                if current_experience is not None:
                    current_experience.description = '\n'.join(description_buffer)
                    experiences.append(current_experience)
                    description_buffer = []
                
                # Start new experience
                current_experience = WorkExperience(
                    title=self._extract_job_title(line),
                    company=self._extract_company(line),
                    start_date="",  # Would need more sophisticated parsing
                    end_date=""
                )
            elif current_experience is not None:
                # Add to description
                description_buffer.append(line)
        
        # Don't forget the last experience
        if current_experience is not None:
            current_experience.description = '\n'.join(description_buffer)
            experiences.append(current_experience)
        
        return experiences
    
    def _is_likely_job_title(self, line: str) -> bool:
        """
        Determine if a line is likely a job title.
        
        Args:
            line: Text line to check
            
        Returns:
            True if line appears to be a job title
        """
        title_keywords = [
            'engineer', 'developer', 'manager', 'director', 'analyst',
            'architect', 'consultant', 'lead', 'senior', 'junior',
            'intern', 'specialist', 'coordinator', 'administrator'
        ]
        
        line_lower = line.lower()
        return any(keyword in line_lower for keyword in title_keywords)
    
    def _extract_job_title(self, line: str) -> str:
        """
        Extract job title from a line.
        
        Args:
            line: Text containing job title
            
        Returns:
            Extracted job title
        """
        # For now, return the line up to common separators
        for sep in [' at ', ' @ ', ' - ', ' | ', ',']:
            if sep in line:
                return line.split(sep)[0].strip()
        return line[:100]  # Limit length
    
    def _extract_company(self, line: str) -> str:
        """
        Extract company name from a line.
        
        Args:
            line: Text containing company name
            
        Returns:
            Extracted company name
        """
        # Look for company after common separators
        for sep in [' at ', ' @ ']:
            if sep in line.lower():
                parts = re.split(sep, line, flags=re.IGNORECASE)
                if len(parts) > 1:
                    # Take the part after separator, clean it up
                    company = parts[1].strip()
                    # Remove date information if present
                    company = re.sub(r'\s*\(.*\)', '', company)
                    company = re.sub(r'\s*\d{4}\s*[-–—]\s*.*', '', company)
                    return company[:100]
        return ""
    
    def _extract_certifications(self, text: str) -> list:
        """
        Extract certifications from text.
        
        Args:
            text: Text from certifications section or full resume
            
        Returns:
            List of Certification objects
        """
        certs = []
        
        # Common certification patterns
        cert_patterns = [
            r'(AWS\s+(?:Certified|Solutions\s+Architect|Developer|SysOps)[^\n,]*)',
            r'(Azure\s+(?:Administrator|Developer|Solutions\s+Architect)[^\n,]*)',
            r'(Google\s+Cloud\s+(?:Professional|Associate)[^\n,]*)',
            r'(PMP|Project\s+Management\s+Professional)',
            r'(CISSP|Certified\s+Information\s+Systems\s+Security\s+Professional)',
            r'(CompTIA\s+\w+)',
            r'(Certified\s+\w+\s+(?:Developer|Engineer|Administrator|Professional)[^\n,]*)',
        ]
        
        for pattern in cert_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                cert_name = match.group(1).strip()
                certs.append(Certification(name=cert_name))
        
        return certs
    
    def _calculate_total_experience(self, experiences: list) -> Optional[float]:
        """
        Calculate total years of experience from work history.
        
        Args:
            experiences: List of WorkExperience objects
            
        Returns:
            Total years of experience, or None if cannot be calculated
        """
        if not experiences:
            return None
        
        # For now, return a rough estimate based on number of positions
        # A more sophisticated version would parse dates
        total_months = 0
        for exp in experiences:
            if exp.duration_months:
                total_months += exp.duration_months
            else:
                # Assume average of 2 years per position if no dates
                total_months += 24
        
        return round(total_months / 12, 1) if total_months > 0 else None
    
    def _estimate_ats_friendliness(self, result: ResumeData, text: str) -> float:
        """
        Estimate how ATS-friendly the resume is.
        
        Uses heuristics based on:
        - Section detection success
        - Presence of bullet points
        - Contact information presence
        - Text complexity
        
        Args:
            result: Parsed ResumeData
            text: Original text
            
        Returns:
            Score from 0 to 1
        """
        score = 0.5  # Start at neutral
        
        # Positive factors
        if result.has_clear_headings:
            score += 0.1
        if result.has_bullet_points:
            score += 0.1
        if result.has_email:
            score += 0.05
        if result.has_phone:
            score += 0.05
        if len(result.skills) > 5:
            score += 0.1
        if result.experience:
            score += 0.1
        
        # Negative factors
        if '[Note:' in text or '[Warning:' in text:
            score -= 0.2  # Indicates parsing issues
        if len(result.sections_detected) < 2:
            score -= 0.15
        
        # Clamp to 0-1
        return max(0.0, min(1.0, score))


# Convenience function for simple usage
def parse_resume(file_content: bytes, filename: str) -> ResumeData:
    """
    Parse a resume file and return structured data.
    
    Args:
        file_content: Raw bytes of the resume file
        filename: Original filename
        
    Returns:
        ResumeData object with extracted information
    """
    parser = ResumeParser()
    return parser.parse_file(file_content, filename)


def parse_resume_text(text: str) -> ResumeData:
    """
    Parse resume text and return structured data.
    
    Args:
        text: Resume content as plain text
        
    Returns:
        ResumeData object with extracted information
    """
    parser = ResumeParser()
    return parser.parse_text(text)
