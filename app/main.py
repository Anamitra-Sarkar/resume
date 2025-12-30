#!/usr/bin/env python3
"""
Resume ↔ Job Match Analyzer - Main CLI Entry Point

A privacy-first, stateless resume analysis tool that compares resumes
against job descriptions and provides actionable, explainable feedback.

Usage:
    python -m app.main analyze resume.pdf job.txt
    python -m app.main analyze resume.pdf job.txt --output report.md
    python -m app.main analyze resume.pdf job.txt --format json --output report.json

Features:
    - Parses PDF, DOCX, and TXT resumes
    - Extracts skills, experience, education
    - Matches against job requirements
    - Provides ATS compatibility analysis
    - Generates comprehensive reports

No data is stored. All processing is done in-memory.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .parser.resume_parser import ResumeParser
from .analyzer.job_analyzer import JobDescriptionAnalyzer
from .scorer.match_scorer import MatchScorer
from .report.report_generator import ReportGenerator


def main():
    """Main entry point for CLI."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    if args.command == "analyze":
        run_analysis(args)
    elif args.command == "parse-resume":
        run_parse_resume(args)
    elif args.command == "parse-job":
        run_parse_job(args)
    else:
        parser.print_help()
        sys.exit(1)


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="resume-analyzer",
        description="Privacy-first Resume ↔ Job Match Analyzer",
        epilog="No data is stored. All processing is done in-memory."
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze a resume against a job description"
    )
    analyze_parser.add_argument(
        "resume",
        help="Path to resume file (PDF, DOCX, or TXT)"
    )
    analyze_parser.add_argument(
        "job",
        help="Path to job description file (TXT) or job description text"
    )
    analyze_parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    analyze_parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json", "pdf", "text"],
        default="markdown",
        help="Output format (default: markdown)"
    )
    analyze_parser.add_argument(
        "--brief", "-b",
        action="store_true",
        help="Generate brief summary instead of full report"
    )
    
    # Parse resume command (for debugging/testing)
    parse_resume_parser = subparsers.add_parser(
        "parse-resume",
        help="Parse a resume and show extracted data"
    )
    parse_resume_parser.add_argument(
        "resume",
        help="Path to resume file"
    )
    parse_resume_parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    
    # Parse job command (for debugging/testing)
    parse_job_parser = subparsers.add_parser(
        "parse-job",
        help="Parse a job description and show extracted data"
    )
    parse_job_parser.add_argument(
        "job",
        help="Path to job description file or text"
    )
    parse_job_parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        help="Output format"
    )
    
    return parser


def run_analysis(args):
    """Run the main analysis workflow."""
    print("🔍 Resume ↔ Job Match Analyzer", file=sys.stderr)
    print("=" * 40, file=sys.stderr)
    print("", file=sys.stderr)
    
    # Read resume
    print("📄 Reading resume...", file=sys.stderr)
    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(f"Error: Resume file not found: {args.resume}", file=sys.stderr)
        sys.exit(1)
    
    resume_content = resume_path.read_bytes()
    
    # Read job description
    print("📋 Reading job description...", file=sys.stderr)
    job_path = Path(args.job)
    if job_path.exists():
        job_text = job_path.read_text(encoding='utf-8')
    else:
        # Assume it's raw text if file doesn't exist
        job_text = args.job
    
    # Parse resume
    print("🔄 Parsing resume...", file=sys.stderr)
    resume_parser = ResumeParser()
    resume_data = resume_parser.parse_file(resume_content, resume_path.name)
    
    print(f"   Found {len(resume_data.skills)} skills", file=sys.stderr)
    print(f"   Found {len(resume_data.experience)} experience entries", file=sys.stderr)
    
    # Parse job description
    print("🔄 Analyzing job description...", file=sys.stderr)
    job_analyzer = JobDescriptionAnalyzer()
    job_data = job_analyzer.analyze(job_text)
    
    print(f"   Found {len(job_data.required_skills)} required skills", file=sys.stderr)
    print(f"   Found {len(job_data.preferred_skills)} preferred skills", file=sys.stderr)
    
    # Calculate match
    print("📊 Calculating match scores...", file=sys.stderr)
    scorer = MatchScorer()
    result = scorer.calculate_match(resume_data, job_data)
    
    print("", file=sys.stderr)
    print(f"✅ Overall Score: {result.overall_score:.0f}/100 (Grade: {result.overall_grade})", file=sys.stderr)
    print("", file=sys.stderr)
    
    # Generate report
    print("📝 Generating report...", file=sys.stderr)
    generator = ReportGenerator()
    
    if args.format == "markdown" or args.format == "text":
        report = generator.generate_markdown(
            result, resume_data, job_data,
            include_details=not args.brief
        )
    elif args.format == "json":
        report = generator.generate_json(result, resume_data, job_data)
    elif args.format == "pdf":
        report = generator.generate_pdf(result, resume_data, job_data)
    else:
        print(f"Error: Unknown format: {args.format}", file=sys.stderr)
        sys.exit(1)
    
    # Output report
    if args.output:
        output_path = Path(args.output)
        if args.format == "pdf":
            output_path.write_bytes(report)
        else:
            output_path.write_text(report, encoding='utf-8')
        print(f"📄 Report saved to: {args.output}", file=sys.stderr)
    else:
        if args.format == "pdf":
            print("Error: PDF output requires --output file path", file=sys.stderr)
            sys.exit(1)
        print(report)
    
    print("", file=sys.stderr)
    print("✨ Analysis complete! No data was stored.", file=sys.stderr)


def run_parse_resume(args):
    """Parse and display resume data."""
    resume_path = Path(args.resume)
    if not resume_path.exists():
        print(f"Error: Resume file not found: {args.resume}", file=sys.stderr)
        sys.exit(1)
    
    resume_content = resume_path.read_bytes()
    
    parser = ResumeParser()
    data = parser.parse_file(resume_content, resume_path.name)
    
    if args.format == "json":
        import json
        output = {
            "skills": [s.normalized_name for s in data.skills],
            "education": [{"degree": e.degree, "field": e.field_of_study} for e in data.education],
            "experience_count": len(data.experience),
            "sections_detected": data.sections_detected,
            "has_email": data.has_email,
            "has_phone": data.has_phone,
            "estimated_years": data.total_years_experience,
            "ats_friendliness": data.estimated_ats_friendliness,
        }
        print(json.dumps(output, indent=2))
    else:
        print("Resume Analysis")
        print("=" * 40)
        print(f"Sections Detected: {', '.join(data.sections_detected)}")
        print(f"Skills Found: {len(data.skills)}")
        if data.skills:
            print(f"  - {', '.join(s.normalized_name for s in data.skills[:10])}")
            if len(data.skills) > 10:
                print(f"  - ... and {len(data.skills) - 10} more")
        print(f"Education Entries: {len(data.education)}")
        print(f"Experience Entries: {len(data.experience)}")
        print(f"Estimated Years: {data.total_years_experience}")
        print(f"ATS Friendliness: {data.estimated_ats_friendliness:.2f}")


def run_parse_job(args):
    """Parse and display job description data."""
    job_path = Path(args.job)
    if job_path.exists():
        job_text = job_path.read_text(encoding='utf-8')
    else:
        job_text = args.job
    
    analyzer = JobDescriptionAnalyzer()
    data = analyzer.analyze(job_text)
    
    if args.format == "json":
        import json
        output = {
            "title": data.title,
            "seniority": data.seniority.value if data.seniority else None,
            "required_skills": [r.skill.normalized_name for r in data.required_skills],
            "preferred_skills": [r.skill.normalized_name for r in data.preferred_skills],
            "min_years": data.min_years_experience,
            "max_years": data.max_years_experience,
            "degree_required": data.degree_required,
            "implicit_expectations": data.implicit_expectations,
            "culture_signals": data.culture_signals,
        }
        print(json.dumps(output, indent=2))
    else:
        print("Job Description Analysis")
        print("=" * 40)
        print(f"Title: {data.title}")
        print(f"Seniority: {data.seniority.value if data.seniority else 'Unknown'}")
        print(f"Experience Required: {data.min_years_experience}-{data.max_years_experience} years")
        print(f"Required Skills ({len(data.required_skills)}):")
        for req in data.required_skills[:10]:
            print(f"  - {req.skill.normalized_name}")
        print(f"Preferred Skills ({len(data.preferred_skills)}):")
        for req in data.preferred_skills[:5]:
            print(f"  - {req.skill.normalized_name}")
        print(f"Implicit Expectations: {', '.join(data.implicit_expectations)}")
        print(f"Culture Signals: {', '.join(data.culture_signals)}")


if __name__ == "__main__":
    main()
