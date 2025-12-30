"""
Report Generator

This module generates comprehensive analysis reports in multiple formats:
- Markdown (.md) - Human-readable, works well in GitHub, editors, etc.
- JSON - Machine-readable for programmatic consumption
- PDF - Formal document for printing/sharing

Reports include:
- Executive summary
- Detailed score breakdown
- Skill analysis (matches, gaps)
- ATS compatibility assessment
- Actionable improvement suggestions
- Improvement checklist
"""

import json
from datetime import datetime
from typing import Optional
from io import BytesIO

from ..models import MatchResult, ResumeData, JobDescriptionData


class ReportGenerator:
    """
    Generates analysis reports in various formats.
    
    All generation is stateless - reports are created in memory
    and returned as strings or bytes. No files are stored.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        pass
    
    def generate_markdown(
        self,
        result: MatchResult,
        resume: ResumeData,
        job: JobDescriptionData,
        include_details: bool = True
    ) -> str:
        """
        Generate a comprehensive Markdown report.
        
        Args:
            result: Match analysis result
            resume: Original resume data
            job: Original job description data
            include_details: Include detailed breakdowns
            
        Returns:
            Markdown-formatted report string
        """
        lines = []
        
        # Header
        lines.append("# Resume ↔ Job Match Analysis Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        if job.title:
            lines.append(f"**Target Position:** {job.title}")
        lines.append("")
        
        # Executive Summary
        lines.append("## 📊 Executive Summary")
        lines.append("")
        lines.append(f"### Overall Match Score: {result.overall_score:.0f}/100 (Grade: {result.overall_grade})")
        lines.append("")
        lines.append(self._get_score_interpretation(result.overall_score))
        lines.append("")
        
        # Score Breakdown
        lines.append("## 📈 Score Breakdown")
        lines.append("")
        lines.append("| Category | Score | Weight | Contribution |")
        lines.append("|----------|-------|--------|--------------|")
        
        for name, breakdown in [
            ("Skill Match", result.skill_match_score),
            ("Experience", result.experience_score),
            ("Keyword Coverage", result.keyword_coverage_score),
            ("ATS Compatibility", result.ats_score),
        ]:
            contribution = breakdown.score * breakdown.weight
            lines.append(
                f"| {name} | {breakdown.score:.0f}/100 | "
                f"{breakdown.weight*100:.0f}% | {contribution:.1f} |"
            )
        
        lines.append("")
        
        if include_details:
            # Detailed Score Analysis
            lines.append("### Skill Match Score Details")
            lines.append("")
            lines.append(f"> {result.skill_match_score.explanation}")
            lines.append("")
            
            if result.skill_match_score.positive_factors:
                lines.append("**Strengths:**")
                for factor in result.skill_match_score.positive_factors:
                    lines.append(f"- ✅ {factor}")
                lines.append("")
            
            if result.skill_match_score.negative_factors:
                lines.append("**Areas for Improvement:**")
                for factor in result.skill_match_score.negative_factors:
                    lines.append(f"- ⚠️ {factor}")
                lines.append("")
        
        # Skill Analysis
        lines.append("## 🎯 Skill Analysis")
        lines.append("")
        
        # Matched Skills
        if result.matched_skills:
            lines.append("### ✅ Matched Skills")
            lines.append("")
            lines.append("| Resume Skill | Job Requirement | Match Type | Confidence |")
            lines.append("|--------------|-----------------|------------|------------|")
            
            for match in result.matched_skills[:15]:  # Limit for readability
                job_skill = match.job_requirement.skill.normalized_name if match.job_requirement else "N/A"
                lines.append(
                    f"| {match.resume_skill.normalized_name} | {job_skill} | "
                    f"{match.match_type} | {match.match_score*100:.0f}% |"
                )
            lines.append("")
        
        # Missing Required Skills
        if result.missing_required_skills:
            lines.append("### ❌ Missing Required Skills")
            lines.append("")
            lines.append("These skills are required by the job but not found in your resume:")
            lines.append("")
            for skill in result.missing_required_skills:
                lines.append(f"- **{skill.normalized_name}**")
            lines.append("")
        
        # Missing Preferred Skills
        if result.missing_preferred_skills:
            lines.append("### 📝 Missing Preferred Skills")
            lines.append("")
            lines.append("These skills are nice-to-have but not critical:")
            lines.append("")
            for skill in result.missing_preferred_skills[:10]:
                lines.append(f"- {skill.normalized_name}")
            lines.append("")
        
        # ATS Analysis
        lines.append("## 🤖 ATS Compatibility")
        lines.append("")
        lines.append(f"**ATS Score:** {result.ats_score.score:.0f}/100")
        lines.append("")
        
        if result.ats_issues:
            lines.append("### Issues Detected")
            lines.append("")
            for issue in result.ats_issues:
                severity_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.severity, "⚪")
                lines.append(f"#### {severity_icon} {issue.title}")
                lines.append(f"{issue.description}")
                lines.append("")
                lines.append(f"**Suggestion:** {issue.suggestion}")
                if issue.example:
                    lines.append(f"**Example:** {issue.example}")
                lines.append("")
        else:
            lines.append("✅ No significant ATS issues detected!")
            lines.append("")
        
        # Improvement Suggestions
        lines.append("## 💡 Improvement Suggestions")
        lines.append("")
        
        if result.quick_wins:
            lines.append("### 🚀 Quick Wins (High Impact, Easy to Implement)")
            lines.append("")
            for suggestion in result.quick_wins:
                lines.append(f"#### {suggestion.title}")
                lines.append(f"{suggestion.description}")
                if suggestion.example:
                    lines.append(f"")
                    lines.append(f"*Example: {suggestion.example}*")
                lines.append("")
        
        if result.long_term_improvements:
            lines.append("### 📈 Long-term Improvements")
            lines.append("")
            for suggestion in result.long_term_improvements:
                lines.append(f"- **{suggestion.title}:** {suggestion.description}")
            lines.append("")
        
        # Bullet Rewrite Examples
        if result.bullet_rewrite_examples:
            lines.append("### ✍️ Bullet Point Rewrite Examples")
            lines.append("")
            for example in result.bullet_rewrite_examples:
                lines.append(f"**Skill to add:** {example['skill']}")
                lines.append("")
                lines.append(f"Before: *{example['before']}*")
                lines.append("")
                lines.append(f"After: **{example['after']}**")
                lines.append("")
                lines.append(f"_{example['explanation']}_")
                lines.append("")
                lines.append("---")
                lines.append("")
        
        # Skill Placement Suggestions
        if result.skill_placement_suggestions:
            lines.append("### 📍 Where to Add Missing Skills")
            lines.append("")
            for suggestion in result.skill_placement_suggestions:
                lines.append(f"- {suggestion}")
            lines.append("")
        
        # Improvement Checklist
        lines.append("## ✅ Improvement Checklist")
        lines.append("")
        lines.append("Use this checklist to track your resume improvements:")
        lines.append("")
        
        # Generate checklist items
        checklist_items = self._generate_checklist(result)
        for item in checklist_items:
            lines.append(f"- [ ] {item}")
        lines.append("")
        
        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*This report was generated by Resume ↔ Job Match Analyzer. "
                    "No data was stored during this analysis.*")
        
        return "\n".join(lines)
    
    def generate_json(
        self,
        result: MatchResult,
        resume: ResumeData,
        job: JobDescriptionData
    ) -> str:
        """
        Generate a JSON report for programmatic consumption.
        
        Args:
            result: Match analysis result
            resume: Original resume data
            job: Original job description data
            
        Returns:
            JSON-formatted report string
        """
        report = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "job_title": job.title,
                "job_seniority": job.seniority.value if job.seniority else None,
            },
            "summary": {
                "overall_score": result.overall_score,
                "grade": result.overall_grade,
                "interpretation": self._get_score_interpretation(result.overall_score),
            },
            "scores": {
                "skill_match": {
                    "score": result.skill_match_score.score,
                    "weight": result.skill_match_score.weight,
                    "explanation": result.skill_match_score.explanation,
                    "positive_factors": result.skill_match_score.positive_factors,
                    "negative_factors": result.skill_match_score.negative_factors,
                    "suggestions": result.skill_match_score.improvement_suggestions,
                },
                "experience": {
                    "score": result.experience_score.score,
                    "weight": result.experience_score.weight,
                    "explanation": result.experience_score.explanation,
                    "positive_factors": result.experience_score.positive_factors,
                    "negative_factors": result.experience_score.negative_factors,
                    "suggestions": result.experience_score.improvement_suggestions,
                },
                "keyword_coverage": {
                    "score": result.keyword_coverage_score.score,
                    "weight": result.keyword_coverage_score.weight,
                    "explanation": result.keyword_coverage_score.explanation,
                    "positive_factors": result.keyword_coverage_score.positive_factors,
                    "negative_factors": result.keyword_coverage_score.negative_factors,
                    "suggestions": result.keyword_coverage_score.improvement_suggestions,
                },
                "ats_compatibility": {
                    "score": result.ats_score.score,
                    "weight": result.ats_score.weight,
                    "explanation": result.ats_score.explanation,
                    "positive_factors": result.ats_score.positive_factors,
                    "negative_factors": result.ats_score.negative_factors,
                    "suggestions": result.ats_score.improvement_suggestions,
                },
            },
            "skills": {
                "matched": [
                    {
                        "resume_skill": m.resume_skill.normalized_name,
                        "job_skill": m.job_requirement.skill.normalized_name if m.job_requirement else None,
                        "match_type": m.match_type,
                        "confidence": m.match_score,
                    }
                    for m in result.matched_skills
                ],
                "missing_required": [s.normalized_name for s in result.missing_required_skills],
                "missing_preferred": [s.normalized_name for s in result.missing_preferred_skills],
                "irrelevant": [s.normalized_name for s in result.irrelevant_skills],
            },
            "ats_issues": [
                {
                    "category": issue.category,
                    "severity": issue.severity,
                    "title": issue.title,
                    "description": issue.description,
                    "suggestion": issue.suggestion,
                }
                for issue in result.ats_issues
            ],
            "improvements": {
                "quick_wins": [
                    {
                        "title": s.title,
                        "description": s.description,
                        "category": s.category,
                        "priority": s.priority,
                        "example": s.example,
                    }
                    for s in result.quick_wins
                ],
                "long_term": [
                    {
                        "title": s.title,
                        "description": s.description,
                        "category": s.category,
                        "priority": s.priority,
                    }
                    for s in result.long_term_improvements
                ],
                "bullet_examples": result.bullet_rewrite_examples,
                "skill_placement": result.skill_placement_suggestions,
            },
        }
        
        return json.dumps(report, indent=2)
    
    def generate_pdf(
        self,
        result: MatchResult,
        resume: ResumeData,
        job: JobDescriptionData
    ) -> bytes:
        """
        Generate a PDF report.
        
        Uses reportlab to create a professional PDF document.
        
        Args:
            result: Match analysis result
            resume: Original resume data
            job: Original job description data
            
        Returns:
            PDF file content as bytes
        """
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            )
            from reportlab.lib import colors
        except ImportError:
            # Return error message if reportlab not available
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            )
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=12
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12
        )
        body_style = styles['Normal']
        
        # Build document content
        elements = []
        
        # Title
        elements.append(Paragraph("Resume ↔ Job Match Analysis Report", title_style))
        elements.append(Spacer(1, 0.25*inch))
        
        # Summary
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Paragraph(
            f"<b>Overall Match Score:</b> {result.overall_score:.0f}/100 "
            f"(Grade: {result.overall_grade})",
            body_style
        ))
        elements.append(Paragraph(
            self._get_score_interpretation(result.overall_score),
            body_style
        ))
        elements.append(Spacer(1, 0.2*inch))
        
        # Score Table
        elements.append(Paragraph("Score Breakdown", heading_style))
        
        score_data = [
            ["Category", "Score", "Weight"],
            ["Skill Match", f"{result.skill_match_score.score:.0f}", f"{result.skill_match_score.weight*100:.0f}%"],
            ["Experience", f"{result.experience_score.score:.0f}", f"{result.experience_score.weight*100:.0f}%"],
            ["Keywords", f"{result.keyword_coverage_score.score:.0f}", f"{result.keyword_coverage_score.weight*100:.0f}%"],
            ["ATS", f"{result.ats_score.score:.0f}", f"{result.ats_score.weight*100:.0f}%"],
        ]
        
        score_table = Table(score_data, colWidths=[2.5*inch, 1*inch, 1*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        elements.append(score_table)
        elements.append(Spacer(1, 0.2*inch))
        
        # Missing Skills
        if result.missing_required_skills:
            elements.append(Paragraph("Missing Required Skills", heading_style))
            skills_text = ", ".join([s.normalized_name for s in result.missing_required_skills[:10]])
            elements.append(Paragraph(skills_text, body_style))
            elements.append(Spacer(1, 0.1*inch))
        
        # Quick Wins
        if result.quick_wins:
            elements.append(Paragraph("Quick Improvement Actions", heading_style))
            for i, suggestion in enumerate(result.quick_wins[:5], 1):
                elements.append(Paragraph(
                    f"{i}. <b>{suggestion.title}:</b> {suggestion.description}",
                    body_style
                ))
            elements.append(Spacer(1, 0.1*inch))
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        elements.append(Paragraph(
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            "No data stored during analysis",
            styles['Italic']
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Get content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _get_score_interpretation(self, score: float) -> str:
        """
        Get human-readable interpretation of score.
        
        Args:
            score: Overall match score
            
        Returns:
            Interpretation string
        """
        if score >= 90:
            return ("Excellent match! Your resume is very well-aligned with this job. "
                   "Focus on highlighting your most relevant experience.")
        elif score >= 75:
            return ("Good match! You have most of what this job requires. "
                   "A few targeted improvements could make your application even stronger.")
        elif score >= 60:
            return ("Moderate match. You have some relevant qualifications, but there are gaps. "
                   "Review the missing skills and improvement suggestions carefully.")
        elif score >= 45:
            return ("Below average match. Consider whether this role is the right fit, "
                   "or invest time in developing the required skills.")
        else:
            return ("Low match. This role may require significant additional experience or skills. "
                   "Focus on building the foundational requirements before applying.")
    
    def _generate_checklist(self, result: MatchResult) -> list:
        """
        Generate a checklist of actionable improvement items.
        
        Args:
            result: Match analysis result
            
        Returns:
            List of checklist item strings
        """
        items = []
        
        # Missing skills
        for skill in result.missing_required_skills[:5]:
            items.append(f"Add '{skill.normalized_name}' to skills section (if qualified)")
        
        # ATS issues
        for issue in result.ats_issues:
            if issue.severity == "high":
                items.append(f"Fix: {issue.title}")
        
        # Quick wins
        for suggestion in result.quick_wins[:3]:
            items.append(suggestion.title)
        
        # General improvements
        if result.skill_match_score.score < 70:
            items.append("Review job description for additional keyword opportunities")
        
        if result.ats_score.score < 80:
            items.append("Simplify resume formatting for better ATS parsing")
        
        return items


# Convenience functions
def generate_markdown_report(
    result: MatchResult,
    resume: ResumeData,
    job: JobDescriptionData
) -> str:
    """Generate a Markdown report."""
    generator = ReportGenerator()
    return generator.generate_markdown(result, resume, job)


def generate_json_report(
    result: MatchResult,
    resume: ResumeData,
    job: JobDescriptionData
) -> str:
    """Generate a JSON report."""
    generator = ReportGenerator()
    return generator.generate_json(result, resume, job)


def generate_pdf_report(
    result: MatchResult,
    resume: ResumeData,
    job: JobDescriptionData
) -> bytes:
    """Generate a PDF report."""
    generator = ReportGenerator()
    return generator.generate_pdf(result, resume, job)
