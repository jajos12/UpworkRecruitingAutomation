"""Mock data generator for testing."""

from typing import List
import random
from backend.models import JobCreate, JobCriteriaModel, ProposalCreate, FreelancerProfile


# Sample job titles and descriptions
JOB_TEMPLATES = [
    {
        "title": "Python Developer for API Integration",
        "description": """
We're looking for an experienced Python developer to help integrate multiple third-party APIs into our existing system.

Requirements:
- 3+ years of Python experience
- Experience with RESTful APIs and GraphQL
- Knowledge of FastAPI or Flask
- Strong problem-solving skills

Project duration: 2-3 weeks
Budget: $2000-$3000
""",
        "criteria": {
            "must_have": [
                "Job Success Score >= 90%",
                "Total earnings >= $10,000",
                "Skills include Python",
                "Cover letter is personalized (not generic template)",
                "Timezone within 5 hours of US Eastern"
            ],
            "nice_to_have": [
                {"criterion": "Top Rated or Top Rated Plus", "weight": 20},
                {"criterion": "Has API integration experience in portfolio", "weight": 15},
                {"criterion": "Hourly rate <= $50", "weight": 10},
                {"criterion": "Responds thoughtfully to screening questions", "weight": 15},
            ],
            "red_flags": [
                "Account created less than 6 months ago with no earnings",
                "Job Success Score dropped significantly recently",
                "Cover letter doesn't mention project specifics"
            ]
        }
    },
    {
        "title": "Full Stack Developer - React + Node.js",
        "description": """
We need a full stack developer to build a web application for our startup.

Tech stack:
- Frontend: React, TypeScript
- Backend: Node.js, Express
- Database: PostgreSQL

Must have experience with modern web development practices.
""",
        "criteria": {
            "must_have": [
                "Job Success Score >= 85%",
                "Experience with React and Node.js",
                "Portfolio shows similar projects"
            ],
            "nice_to_have": [
                {"criterion": "Top Rated status", "weight": 15},
                {"criterion": "TypeScript experience", "weight": 10}
            ],
            "red_flags": []
        }
    },
    {
        "title": "Data Analyst - Python & SQL",
        "description": """
Looking for a data analyst to help with our business intelligence needs.

Requirements:
- Strong SQL skills
- Python (pandas, numpy)
- Data visualization (Tableau or similar)
- Experience with ETL pipelines
""",
        "criteria": {
            "must_have": [
                "Job Success Score >= 90%",
                "Strong SQL and Python skills",
                "Data visualization experience"
            ],
            "nice_to_have": [
                {"criterion": "Has worked with large datasets", "weight": 20}
            ],
            "red_flags": []
        }
    }
]


# Sample freelancer profiles
FREELANCER_TEMPLATES = [
    # Tier 1 quality freelancers
    {
        "name": "John Smith",
        "title": "Senior Python Developer | API Integration Specialist",
        "hourly_rate": 45.0,
        "job_success_score": 98,
        "total_earnings": 125000.0,
        "top_rated_status": "Top Rated Plus",
        "skills": ["Python", "FastAPI", "Django", "REST APIs", "GraphQL", "PostgreSQL"],
        "bio": "I am a Senior Backend Engineer with over 10 years of experience specializing in high-performance Python APIs and cloud architecture. I focus on building scalable systems that solve complex business problems. My approach is centered on clean code, robust testing, and clear communication.",
        "certifications": ["AWS Certified Solutions Architect", "Professional Scrum Master I"],
        "portfolio": [
            {"title": "E-commerce Microservices", "desc": "Built a scalable backend for a major retailer using FastAPI and AWS Lambda."},
            {"title": "Real-time Analytics Dashboard", "desc": "Developed a high-throughput data processing pipeline using Kafka and Python."}
        ],
        "work_history_summary": "10+ years of experience building scalable APIs. Recent projects include integrating Stripe, Twilio, and AWS services.",
        "cover_letter_template": "Hi! I noticed your project requires {skill} expertise. I've completed similar work for {previous_client_type}, specifically {specific_achievement}. I'm confident I can deliver exactly what you need. Let's discuss your requirements in detail.",
        "quality": "high"
    },
    {
        "name": "Sarah Chen",
        "title": "Full Stack Developer | React & Node Expert",
        "hourly_rate": 50.0,
        "job_success_score": 100,
        "total_earnings": 89000.0,
        "top_rated_status": "Top Rated Plus",
        "skills": ["React", "Node.js", "TypeScript", "PostgreSQL", "AWS", "MongoDB"],
        "bio": "Full-stack developer with a passion for building beautiful, intuitive, and performant web applications. I specialize in the React/Node.js ecosystem and have a strong track record of delivering startup MVPs from concept to production.",
        "certifications": ["Google Cloud Professional Developer"],
        "portfolio": [
            {"title": "SaaS Project Management Tool", "desc": "A full-featured team collaboration app built with React, Redux, and Node.js."},
            {"title": "Crypto Portfolio Tracker", "desc": "Real-time tracking app with integrated exchange APIs."}
        ],
        "work_history_summary": "8 years building modern web applications. Specialized in React and Node.js stack.",
        "cover_letter_template": "Hello! Your project caught my attention because {reason}. I have extensive experience with {relevant_skill} and have delivered {achievement}. I'd love to help you achieve {project_goal}.",
        "quality": "high"
    },
    {
        "name": "Ahmed Hassan",
        "title": "Data Analyst & Python Developer",
        "hourly_rate": 40.0,
        "job_success_score": 95,
        "total_earnings": 65000.0,
        "top_rated_status": "Top Rated",
        "skills": ["Python", "SQL", "Pandas", "Tableau", "Data Visualization", "ETL"],
        "bio": "Data enthusiast with 6+ years of experience turning complex datasets into actionable business insights. Expert in Python data stack and SQL optimization. I translate raw data into stories that drive decision-making.",
        "certifications": ["Tableau Desktop Specialist", "Microsoft Certified: Querying Data with SQL Server"],
        "portfolio": [
            {"title": "Customer Churn Analysis", "desc": "Predictive model that reduced churn for a telecom client by 15%."},
            {"title": "Automated ETL Pipeline", "desc": "Reduced reporting latency by 70% using optimized Airflow DAGs."}
        ],
        "work_history_summary": "6 years of data analysis experience. Built ETL pipelines processing millions of records.",
        "cover_letter_template": "Hi there! I'm an experienced data analyst with expertise in {skill}. I've helped {client_type} achieve {result}. Your project requirements align perfectly with my skills.",
        "quality": "high"
    },
    
    # Tier 2 quality freelancers  
    {
        "name": "Maria Garcia",
        "title": "Python Developer",
        "hourly_rate": 35.0,
        "job_success_score": 88,
        "total_earnings": 25000.0,
        "top_rated_status": None,
        "skills": ["Python", "Flask", "MySQL", "JavaScript"],
        "bio": "Enthusiastic Python developer with 3 years of professional experience. I enjoy solving coding challenges and am always eager to learn new technologies. I provide reliable results and maintain good communication throughout the project.",
        "certifications": [],
        "portfolio": [
            {"title": "Personal Blog Engine", "desc": "A simple CMS built with Flask and SQLite."}
        ],
        "work_history_summary": "3 years of Python development. Solid skills but still building portfolio.",
        "cover_letter_template": "Hi! I'm interested in your project. I have experience with {skill} and would be happy to help. Let me know if you'd like to discuss.",
        "quality": "medium"
    },
    {
        "name": "David Lee",
        "title": "Web Developer",
        "hourly_rate": 30.0,
        "job_success_score": 82,
        "total_earnings": 18000.0,
        "top_rated_status": None,
        "skills": ["JavaScript", "React", "HTML", "CSS"],
        "work_history_summary": "2 years of web development experience. Eager to take on new challenges.",
        "cover_letter_template": "Hello, I can help with your project. I have some experience with {skill}. Please let me know if you're interested.",
        "quality": "medium"
    },
    
    # Tier 3 quality freelancers
    {
        "name": "Raj Patel",
        "title": "Developer",
        "hourly_rate": 15.0,
        "job_success_score": 75,
        "total_earnings": 3000.0,
        "top_rated_status": None,
        "skills": ["HTML", "CSS", "Python"],
        "work_history_summary": "Recent Upwork member. Still learning.",
        "cover_letter_template": "I can do your project. I know {skill}. Please hire me.",
        "quality": "low"
    },
    {
        "name": "Generic Freelancer",
        "title": "Software Developer",
        "hourly_rate": 20.0,
        "job_success_score": 68,
        "total_earnings": 5000.0,
        "top_rated_status": None,
        "skills": ["Python", "Java", "C++"],
        "work_history_summary": "Various projects completed.",
        "cover_letter_template": "Dear Hiring Manager, I am very interested in this position. I have many years of experience in software development. I am hardworking and dedicated. Please consider my application. Thank you.",
        "quality": "low"
    }
]


def generate_mock_jobs(count: int = 3) -> List[JobCreate]:
    """Generate mock job postings."""
    jobs = []
    for i, template in enumerate(JOB_TEMPLATES[:count]):
        jobs.append(JobCreate(
            title=template["title"],
            description=template["description"].strip(),
            criteria=JobCriteriaModel(**template["criteria"])
        ))
    return jobs


def seed_mock_data(data_manager, websocket_manager, ai_analyzer=None):
    """
    Seed the database with realistic mock data.
    
    Args:
        data_manager: DataManager instance
        websocket_manager: WebSocketManager instance  
        ai_analyzer: Optional AIAnalyzer instance for analysis
    """
    import asyncio
    
    # Generate mock jobs (returns JobCreate objects)
    mock_jobs_data = generate_mock_jobs()

    # Add jobs to database and generate proposals for them
    for i, job_data in enumerate(mock_jobs_data):
        # Use stable ID for mock data to survive server reloads
        stable_job_id = f"mock_job_{i}"
        job = data_manager.create_job(job_data, job_id=stable_job_id)
        
        # Broadcast job creation
        asyncio.create_task(
            websocket_manager.broadcast_activity(
                event_type="job_created",
                message=f"Created job: {job.title}"
            )
        )
        
        # Add proposals for this job
        proposals_for_job = generate_realistic_proposal_mix(job.job_id, job.title)
        for proposal_data in proposals_for_job:
            # create_proposal expects a ProposalCreate object
            proposal = data_manager.create_proposal(proposal_data)
            
            # Broadcast proposal creation
            asyncio.create_task(
                websocket_manager.broadcast_activity(
                    event_type="proposal_created",
                    message=f"Added proposal from {proposal.freelancer.name} for job '{job.title}'"
                )
            )



def generate_mock_proposal(job_id: str, job_title: str, quality: str = None) -> ProposalCreate:
    """
    Generate a mock proposal for a job.
    
    Args:
        job_id: Job ID
        job_title: Job title (used for cover letter personalization)
        quality: Force quality level (high, medium, low) or random if None
    """
    if quality:
        freelancers = [f for f in FREELANCER_TEMPLATES if f["quality"] == quality]
    else:
        freelancers = FREELANCER_TEMPLATES
    
    template = random.choice(freelancers)
    
    # Create freelancer profile
    freelancer_id = f"freelancer_{random.randint(100000, 999999)}"
    freelancer = FreelancerProfile(
        freelancer_id=freelancer_id,
        name=template["name"],
        title=template["title"],
        hourly_rate=template["hourly_rate"],
        job_success_score=template["job_success_score"],
        total_earnings=template["total_earnings"],
        top_rated_status=template["top_rated_status"],
        skills=template["skills"],
        bio=template.get("bio", ""),
        certifications=template.get("certifications", []),
        portfolio_items=template.get("portfolio", []),
        work_history_summary=template["work_history_summary"],
        profile_url=f"https://upwork.com/freelancers/{freelancer_id}"
    )
    
    # Personalize cover letter based on template
    cover_letter = template["cover_letter_template"].format(
        skill=random.choice(template["skills"]),
        previous_client_type="tech startups" if template["quality"] == "high" else "clients",
        specific_achievement="reducing API latency by 40%" if template["quality"] == "high" else "completing projects on time",
        reason="it aligns with my expertise" if template["quality"] == "high" else "I need work",
        relevant_skill=random.choice(template["skills"]),
        achievement="5-star ratings on similar projects" if template["quality"] == "high" else "several projects",
        project_goal="your goals" if template["quality"] == "high" else "this",
        client_type="enterprise clients" if template["quality"] == "high" else "various clients",
        result="significant cost savings" if template["quality"] == "high" else "good results"
    )
    
    # Bid amount varies based on hourly rate
    bid_amount = template["hourly_rate"] * random.randint(20, 40)
    
    return ProposalCreate(
        job_id=job_id,
        freelancer=freelancer,
        cover_letter=cover_letter,
        bid_amount=bid_amount,
        estimated_duration="2-3 weeks",
        screening_answers="Yes, I have experience with the required technologies."
    )


def generate_realistic_proposal_mix(job_id: str, job_title: str) -> List[ProposalCreate]:
    """
    Generate a realistic mix of proposals for a job.
    
    Typically:
    - 15-20% Tier 1 (high quality)
    - 30-35% Tier 2 (medium quality)
    - 45-55% Tier 3 (low quality)
    """
    proposals = []
    
    # Generate proposals
    total_count = random.randint(8, 15)
    
    for i in range(total_count):
        rand = random.random()
        if rand < 0.15:
            quality = "high"
        elif rand < 0.50:
            quality = "medium"
        else:
            quality = "low"
        
        proposals.append(generate_mock_proposal(job_id, job_title, quality))
    
    return proposals
