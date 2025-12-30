"""
Resume Job Match Analyzer - Skill Knowledge Base

This module contains the knowledge base for skill normalization, synonyms,
and categorization. It provides deterministic, reproducible skill matching.

Design Principles:
1. Explicit mappings over ML-based inference
2. Conservative matching (prefer precision over recall)
3. Easy to extend and audit
"""

# Skill synonyms: Maps various names to a canonical form
# Format: canonical_name -> [aliases]
SKILL_SYNONYMS = {
    # Programming Languages
    "JavaScript": ["JS", "Javascript", "javascript", "ECMAScript", "ES6", "ES2015", "ES2020", "ES2021", "ES2022"],
    "TypeScript": ["TS", "Typescript", "typescript"],
    "Python": ["python", "Python3", "Python 3", "python3", "py"],
    "Java": ["java", "JAVA", "J2EE", "J2SE", "Java SE", "Java EE"],
    "C++": ["CPP", "Cpp", "cpp", "C Plus Plus", "c++"],
    "C#": ["CSharp", "C Sharp", "csharp", "c#"],
    "Go": ["Golang", "golang", "go-lang"],
    "Ruby": ["ruby", "RUBY"],
    "PHP": ["php", "Php", "PHP8", "PHP7"],
    "Swift": ["swift", "SWIFT"],
    "Kotlin": ["kotlin", "KOTLIN"],
    "Rust": ["rust", "RUST"],
    "Scala": ["scala", "SCALA"],
    "R": ["r-lang", "R language", "R programming"],
    "SQL": ["sql", "Sql", "Structured Query Language"],
    "Bash": ["bash", "Shell", "shell", "Shell Scripting", "Bash Scripting", "sh", "zsh"],
    "PowerShell": ["powershell", "Powershell", "PS"],
    "Objective-C": ["ObjC", "Objective C", "objc"],
    
    # Frontend Frameworks
    "React": ["ReactJS", "React.js", "react", "React JS"],
    "Angular": ["AngularJS", "Angular.js", "angular", "Angular 2+", "Angular2"],
    "Vue.js": ["Vue", "VueJS", "vue", "Vue 3", "Vue.js"],
    "Next.js": ["NextJS", "Next", "next.js", "Nextjs"],
    "Svelte": ["svelte", "SvelteKit"],
    "jQuery": ["jquery", "JQuery", "JQUERY"],
    
    # Backend Frameworks
    "Node.js": ["NodeJS", "Node", "node", "Node JS", "nodejs"],
    "Express.js": ["Express", "ExpressJS", "express"],
    "Django": ["django", "DJANGO"],
    "Flask": ["flask", "FLASK"],
    "FastAPI": ["fastapi", "Fast API"],
    "Ruby on Rails": ["Rails", "rails", "RoR", "Ruby Rails"],
    "Spring": ["Spring Boot", "SpringBoot", "Spring Framework", "spring"],
    "ASP.NET": ["ASP", "asp.net", "ASP.NET Core", "ASPNET", ".NET Core"],
    "Laravel": ["laravel", "LARAVEL"],
    
    # Databases
    "PostgreSQL": ["Postgres", "postgres", "PGSQL", "pgsql"],
    "MySQL": ["mysql", "MYSQL", "MariaDB", "mariadb"],
    "MongoDB": ["mongo", "Mongo", "mongodb"],
    "Redis": ["redis", "REDIS"],
    "Elasticsearch": ["ES", "elasticsearch", "Elastic Search"],
    "DynamoDB": ["dynamodb", "Dynamo DB", "Amazon DynamoDB", "AWS DynamoDB"],
    "SQLite": ["sqlite", "sqlite3", "SQLite3"],
    "Oracle": ["oracle", "Oracle DB", "Oracle Database"],
    "Microsoft SQL Server": ["MSSQL", "SQL Server", "MS SQL", "TSQL", "T-SQL"],
    "Cassandra": ["cassandra", "Apache Cassandra"],
    
    # Cloud Platforms
    "Amazon Web Services": ["AWS", "aws", "Amazon Cloud"],
    "Microsoft Azure": ["Azure", "azure", "MS Azure"],
    "Google Cloud Platform": ["GCP", "gcp", "Google Cloud"],
    "Heroku": ["heroku", "HEROKU"],
    "DigitalOcean": ["digitalocean", "Digital Ocean"],
    
    # DevOps & Tools
    "Docker": ["docker", "DOCKER", "Containers", "containerization"],
    "Kubernetes": ["K8s", "k8s", "kubernetes", "K8S", "kube"],
    "Jenkins": ["jenkins", "JENKINS"],
    "GitLab CI": ["GitLab", "gitlab-ci", "GitLab CI/CD"],
    "GitHub Actions": ["GH Actions", "GitHub CI", "Github Actions"],
    "CircleCI": ["circleci", "Circle CI"],
    "Travis CI": ["Travis", "travis-ci", "travis"],
    "Terraform": ["terraform", "TF", "HashiCorp Terraform"],
    "Ansible": ["ansible", "ANSIBLE"],
    "Puppet": ["puppet", "PUPPET"],
    "Chef": ["chef", "CHEF"],
    
    # Version Control
    "Git": ["git", "GIT"],
    "GitHub": ["github", "Github"],
    "GitLab": ["gitlab", "Gitlab"],
    "Bitbucket": ["bitbucket", "Bit Bucket"],
    "SVN": ["Subversion", "svn", "Apache Subversion"],
    
    # Testing
    "Jest": ["jest", "JEST"],
    "Mocha": ["mocha", "MOCHA"],
    "Pytest": ["pytest", "py.test", "PyTest"],
    "JUnit": ["junit", "JUNIT"],
    "Selenium": ["selenium", "SELENIUM", "Selenium WebDriver"],
    "Cypress": ["cypress", "CYPRESS"],
    "Playwright": ["playwright", "PLAYWRIGHT"],
    
    # Machine Learning / Data Science
    "TensorFlow": ["tensorflow", "TF", "Tensor Flow"],
    "PyTorch": ["pytorch", "Py Torch"],
    "scikit-learn": ["sklearn", "Scikit-learn", "scikit learn", "SKLearn"],
    "Pandas": ["pandas", "PANDAS"],
    "NumPy": ["numpy", "Numpy", "NUMPY"],
    "Keras": ["keras", "KERAS"],
    "Apache Spark": ["Spark", "spark", "PySpark", "pyspark"],
    "Hadoop": ["hadoop", "HADOOP", "Apache Hadoop"],
    
    # Web Technologies
    "HTML": ["html", "HTML5", "html5"],
    "CSS": ["css", "CSS3", "css3", "Cascading Style Sheets"],
    "SASS": ["sass", "Sass", "SCSS", "scss"],
    "Less": ["less", "LESS"],
    "REST API": ["REST", "RESTful", "REST APIs", "RESTful API"],
    "GraphQL": ["graphql", "GQL", "Graph QL"],
    "WebSockets": ["websocket", "Websocket", "WS", "Socket.io"],
    
    # Mobile Development
    "React Native": ["ReactNative", "react-native", "RN"],
    "Flutter": ["flutter", "FLUTTER"],
    "Xamarin": ["xamarin", "XAMARIN"],
    "Ionic": ["ionic", "IONIC"],
    
    # Soft Skills
    "Communication": ["communication skills", "verbal communication", "written communication", "interpersonal communication"],
    "Leadership": ["leadership skills", "team leadership", "people management"],
    "Problem Solving": ["problem-solving", "analytical thinking", "critical thinking", "troubleshooting"],
    "Teamwork": ["team player", "collaboration", "collaborative", "team collaboration"],
    "Time Management": ["time-management", "deadline management", "prioritization"],
    "Adaptability": ["flexible", "adaptable", "versatile", "quick learner"],
    "Project Management": ["PM", "project coordination", "program management"],
    "Agile": ["Agile Methodology", "agile", "Scrum", "scrum", "SCRUM", "Kanban", "kanban"],
    
    # Other common tools/technologies
    "Jira": ["jira", "JIRA", "Atlassian Jira"],
    "Confluence": ["confluence", "CONFLUENCE"],
    "Slack": ["slack", "SLACK"],
    "Linux": ["linux", "LINUX", "Unix", "unix", "UNIX"],
    "Windows": ["windows", "Windows Server", "Win"],
    "macOS": ["MacOS", "Mac OS", "OSX", "OS X", "Apple Mac"],
    "Visual Studio Code": ["VS Code", "VSCode", "vscode"],
    "IntelliJ": ["IntelliJ IDEA", "intellij", "IDEA"],
    "Postman": ["postman", "POSTMAN"],
    "Figma": ["figma", "FIGMA"],
    "Adobe XD": ["XD", "Adobe Experience Design"],
    "Sketch": ["sketch", "SKETCH"],
}

# Build reverse lookup: alias -> canonical_name
ALIAS_TO_CANONICAL = {}
for canonical, aliases in SKILL_SYNONYMS.items():
    ALIAS_TO_CANONICAL[canonical.lower()] = canonical
    for alias in aliases:
        ALIAS_TO_CANONICAL[alias.lower()] = canonical

# Skill categories: Maps skills to their category
SKILL_CATEGORIES = {
    # Programming Languages
    "JavaScript": "programming_language",
    "TypeScript": "programming_language",
    "Python": "programming_language",
    "Java": "programming_language",
    "C++": "programming_language",
    "C#": "programming_language",
    "Go": "programming_language",
    "Ruby": "programming_language",
    "PHP": "programming_language",
    "Swift": "programming_language",
    "Kotlin": "programming_language",
    "Rust": "programming_language",
    "Scala": "programming_language",
    "R": "programming_language",
    "SQL": "programming_language",
    
    # Frameworks
    "React": "frontend_framework",
    "Angular": "frontend_framework",
    "Vue.js": "frontend_framework",
    "Next.js": "frontend_framework",
    "Svelte": "frontend_framework",
    "Node.js": "backend_framework",
    "Express.js": "backend_framework",
    "Django": "backend_framework",
    "Flask": "backend_framework",
    "FastAPI": "backend_framework",
    "Spring": "backend_framework",
    "Ruby on Rails": "backend_framework",
    
    # Databases
    "PostgreSQL": "database",
    "MySQL": "database",
    "MongoDB": "database",
    "Redis": "database",
    "Elasticsearch": "database",
    "DynamoDB": "database",
    
    # Cloud
    "Amazon Web Services": "cloud",
    "Microsoft Azure": "cloud",
    "Google Cloud Platform": "cloud",
    
    # DevOps
    "Docker": "devops",
    "Kubernetes": "devops",
    "Jenkins": "devops",
    "Terraform": "devops",
    "Ansible": "devops",
    
    # Soft Skills
    "Communication": "soft_skill",
    "Leadership": "soft_skill",
    "Problem Solving": "soft_skill",
    "Teamwork": "soft_skill",
    "Time Management": "soft_skill",
    "Agile": "methodology",
}

# Semantic groups: Skills that are related/similar
SEMANTIC_GROUPS = {
    "frontend_development": ["React", "Angular", "Vue.js", "JavaScript", "TypeScript", "HTML", "CSS", "SASS"],
    "backend_development": ["Node.js", "Django", "Flask", "FastAPI", "Express.js", "Ruby on Rails", "Spring"],
    "data_engineering": ["Python", "Apache Spark", "Hadoop", "SQL", "PostgreSQL", "MongoDB"],
    "machine_learning": ["Python", "TensorFlow", "PyTorch", "scikit-learn", "Keras", "Pandas", "NumPy"],
    "devops": ["Docker", "Kubernetes", "Jenkins", "Terraform", "Ansible", "GitLab CI", "GitHub Actions"],
    "cloud_computing": ["Amazon Web Services", "Microsoft Azure", "Google Cloud Platform"],
    "mobile_development": ["Swift", "Kotlin", "React Native", "Flutter"],
    "databases": ["PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "DynamoDB"],
}

# Experience level indicators: Words/phrases that suggest experience level
SENIORITY_INDICATORS = {
    "entry": [
        "entry level", "entry-level", "junior", "graduate", "intern", "internship",
        "0-1 years", "0-2 years", "new grad", "recent graduate", "no experience required",
        "associate", "fresher", "trainee"
    ],
    "junior": [
        "junior", "1-2 years", "1-3 years", "early career", "some experience",
        "junior developer", "associate"
    ],
    "mid": [
        "mid-level", "mid level", "2-4 years", "3-5 years", "2-5 years",
        "experienced", "solid experience", "professional experience"
    ],
    "senior": [
        "senior", "5+ years", "5-7 years", "5-10 years", "7+ years",
        "extensive experience", "deep experience", "sr.", "lead"
    ],
    "lead": [
        "lead", "team lead", "tech lead", "technical lead", "architect",
        "8+ years", "10+ years", "leadership"
    ],
    "principal": [
        "principal", "staff", "distinguished", "10+ years", "15+ years",
        "thought leader", "expert level"
    ],
    "executive": [
        "executive", "director", "vp", "vice president", "c-level", "cto", "ceo",
        "head of", "chief"
    ]
}

# Implicit job expectations: Phrases that suggest certain expectations
IMPLICIT_EXPECTATIONS = {
    "fast_paced": [
        "fast-paced", "fast paced", "dynamic environment", "startup",
        "rapidly growing", "high growth", "agile environment"
    ],
    "ownership": [
        "ownership", "take ownership", "end-to-end", "end to end",
        "full ownership", "autonomous", "independently"
    ],
    "collaboration": [
        "cross-functional", "cross functional", "collaborate", "team player",
        "collaborative", "work with teams", "stakeholders"
    ],
    "innovation": [
        "innovative", "cutting-edge", "cutting edge", "greenfield",
        "build from scratch", "new technologies"
    ],
    "scale": [
        "scale", "high-scale", "millions of users", "large scale",
        "high traffic", "performance critical", "high availability"
    ],
    "mentorship": [
        "mentor", "mentoring", "coach", "guide junior", "develop talent",
        "grow the team", "knowledge sharing"
    ]
}

# Common resume section headers (for section detection)
SECTION_HEADERS = {
    "experience": [
        "experience", "work experience", "professional experience", "employment history",
        "work history", "career history", "relevant experience"
    ],
    "education": [
        "education", "academic background", "qualifications", "degrees",
        "educational background", "academic qualifications"
    ],
    "skills": [
        "skills", "technical skills", "competencies", "core competencies",
        "expertise", "proficiencies", "technologies", "tech stack"
    ],
    "projects": [
        "projects", "personal projects", "side projects", "portfolio",
        "notable projects", "key projects"
    ],
    "certifications": [
        "certifications", "certificates", "credentials", "professional certifications",
        "licenses"
    ],
    "summary": [
        "summary", "professional summary", "profile", "about", "objective",
        "career objective", "professional profile", "about me"
    ],
    "achievements": [
        "achievements", "accomplishments", "awards", "honors", "recognition"
    ],
    "publications": [
        "publications", "papers", "research", "articles"
    ],
    "languages": [
        "languages", "language skills", "spoken languages"
    ]
}

# Degree equivalents and levels
DEGREE_LEVELS = {
    "phd": ["phd", "ph.d", "doctorate", "doctor of philosophy", "dphil", "doctoral"],
    "masters": ["masters", "master's", "ms", "m.s.", "ma", "m.a.", "mba", "m.b.a.", 
                "msc", "m.sc.", "meng", "m.eng."],
    "bachelors": ["bachelors", "bachelor's", "bs", "b.s.", "ba", "b.a.", "bsc", 
                  "b.sc.", "beng", "b.eng.", "undergraduate"],
    "associate": ["associate", "associates", "associate's", "as", "a.s.", "aa", "a.a."],
    "bootcamp": ["bootcamp", "boot camp", "coding bootcamp", "certificate program"],
}


def normalize_skill(skill_text: str) -> str:
    """
    Normalize a skill name to its canonical form.
    
    Args:
        skill_text: Raw skill text from resume or job description
        
    Returns:
        Canonical skill name, or original text if no match found
    """
    # Clean the input
    cleaned = skill_text.strip()
    lookup_key = cleaned.lower()
    
    # Direct lookup
    if lookup_key in ALIAS_TO_CANONICAL:
        return ALIAS_TO_CANONICAL[lookup_key]
    
    # Return original (title-cased) if no match
    return cleaned


def get_skill_category(skill_name: str) -> str:
    """
    Get the category for a skill.
    
    Args:
        skill_name: Canonical skill name
        
    Returns:
        Category string, or "other" if unknown
    """
    return SKILL_CATEGORIES.get(skill_name, "other")


def find_semantic_matches(skill_name: str) -> list:
    """
    Find skills that are semantically related to the given skill.
    
    Args:
        skill_name: Canonical skill name
        
    Returns:
        List of related skill names
    """
    related = []
    for group_name, skills in SEMANTIC_GROUPS.items():
        if skill_name in skills:
            # Add all other skills in this group
            related.extend([s for s in skills if s != skill_name])
    return list(set(related))


def detect_seniority(text: str) -> str:
    """
    Detect seniority level from text.
    
    Args:
        text: Job description or title text
        
    Returns:
        Seniority level string
    """
    text_lower = text.lower()
    
    # Check in order from most senior to least
    for level in ["executive", "principal", "lead", "senior", "mid", "junior", "entry"]:
        for indicator in SENIORITY_INDICATORS[level]:
            if indicator in text_lower:
                return level
    
    return "unknown"
