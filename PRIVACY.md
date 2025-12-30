# Privacy Policy

## Overview

Resume ↔ Job Match Analyzer is designed from the ground up with privacy as a core principle. We believe that your resume and job search information is deeply personal, and we've built this tool to ensure that your data stays yours.

## Our Commitments

### ❌ What We Do NOT Do

1. **No Data Storage**
   - We do not store your resume content anywhere
   - We do not store job descriptions you analyze
   - We do not store analysis results on any server
   - We do not use any database (no MongoDB, PostgreSQL, SQLite, Redis, or any other)

2. **No Tracking**
   - We do not use analytics cookies
   - We do not track your usage patterns
   - We do not collect any personally identifiable information
   - We do not integrate with any third-party analytics services

3. **No Accounts**
   - We do not require user registration
   - We do not maintain user profiles
   - We do not track sessions across visits
   - We do not store any authentication credentials

4. **No External Sharing**
   - We do not share your data with third parties
   - We do not sell your information
   - We do not use your resume to train any models
   - We do not send your data to external APIs

### ✅ What We DO Do

1. **In-Memory Processing**
   - All resume parsing happens in memory
   - All analysis is computed on-the-fly
   - All results are generated in real-time

2. **Immediate Deletion**
   - Uploaded files are processed and immediately discarded
   - Any temporary files created during processing are automatically deleted
   - When you close the browser or terminate the CLI, all data is gone

3. **User-Initiated Downloads**
   - Reports are only created when you request them
   - Downloads are served directly to your device
   - We do not retain copies of generated reports

4. **Transparent Processing**
   - All analysis algorithms are deterministic and reproducible
   - We use rule-based matching, not opaque ML models
   - You can inspect our source code to verify our claims

## Technical Implementation

### API Mode
When using the web API:
- Files are read into memory and processed
- Response is sent directly to the client
- No logging of request/response bodies
- File handles are explicitly closed after processing

### CLI Mode
When using the command-line interface:
- Files are read from your local filesystem
- Processing happens entirely on your machine
- Reports are written to your local filesystem
- No network requests are made

### Library Mode
When importing as a Python library:
- You have full control over the data flow
- No implicit storage or transmission
- All objects are standard Python objects in your process memory

## Open Source Transparency

This project is open source. You can:
- Review our code to verify privacy claims
- Run the tool entirely on your own infrastructure
- Modify the code to meet your specific needs
- Audit the dependencies we use

## File Format Security

### What We Extract
- Text content from resumes
- Structural information (sections, formatting)
- Skills and experience mentions

### What We Ignore
- Embedded macros or scripts
- External links (we detect but don't follow them)
- Hidden metadata beyond what's needed for parsing

## Self-Hosting

For maximum privacy, you can:

1. **Run locally**: No network access required
   ```bash
   python -m app.main analyze resume.pdf job.txt
   ```

2. **Self-host the API**: Full control over your infrastructure
   ```bash
   uvicorn app.api:app --host 127.0.0.1 --port 8000
   ```

3. **Air-gapped usage**: The tool works without internet access

## Questions or Concerns?

If you have any privacy-related questions or concerns about this tool:

1. **Review the source code** - It's all open source
2. **Open an issue** - We're happy to discuss privacy concerns publicly
3. **Contribute improvements** - Help us make the tool even more private

## Summary

| Aspect | Status |
|--------|--------|
| Data storage | ❌ None |
| User accounts | ❌ None |
| Analytics tracking | ❌ None |
| Third-party sharing | ❌ None |
| Resume content logging | ❌ None |
| In-memory processing | ✅ Yes |
| Local execution option | ✅ Yes |
| Open source | ✅ Yes |
| Deterministic processing | ✅ Yes |

---

**Your resume is yours. We just help you improve it.**

*Last updated: 2024*
