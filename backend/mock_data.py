"""Mock data generator for testing."""

from typing import List
import random
from backend.models import JobCreate, JobCriteriaModel, ProposalCreate, FreelancerProfile


# Sample job titles and descriptions
# Sample job titles and descriptions
JOB_TEMPLATES = [
    {
        "title": "Parents That are Really Struggling With Their Child's Phone/Screen Use",
        "description": """
We're trying to build a solution to help parents protect their kids from the negative effects of smartphones and modern technology/screen time.

But before getting too settled in on our specific style of solution:

**We're looking for parents who are genuinely very concerned about how their child's phone or internet use is affecting them** — their attention spans, mood, sleep, focus, grades, friendships, safety, or anything else to help us gain more empathy for the problems facing kids and their parents today.

If this is something that keeps you up at night, we want to hear from you!!

---

**What you'll do:**

Either take calls with our team or perhaps record a voice memo answering a few open-ended questions about your experience here. We would love for you to just brain dump all of your feelings and pain points to us, it can be a very unstructured stream of consciousness brain dump of all your thoughts and feelings about the topic that you can immediately do whenever it is convenient for you. Don’t feel shy or worried about it at all, it will be very easy and low stress, we will send you some prompts to discuss about and then you can record the voice memo and send it over. Over time we will continuously ask for more and more information from you that you can send us in this format too.

All we want is honesty and real world opinions from you and perhaps a connection with anyone you might know that also has any of these problems with their kids and smartphones nowadays.

We want to hear:
- What's been happening with your child
- What you've tried
- What's worked, what hasn't
- How urgent and painful this feels for you
- How damaging you believe it might be for you kid.

---

**Who we're looking for:**
- Parents of children under 18
- You're actively concerned (not just "mildly annoyed") about your child's phone, tablet, gaming, or social media use
- Based in the US, UK, Canada, or Australia
- Comfortable recording a voice memo in English

---

**This is NOT for you IF:**
- Screens aren't really a concern in your household
- You've got it mostly figured out and things are going fine

Less than 30 hrs/week
Hourly: $5.00 - $25.00
Duration: 1 to 3 months
Experience Level: Intermediate
""",
        "criteria": {
            "must_have": [
                "Location is US, UK, Canada, or Australia",
                "Parent of child under 18",
                "Concerned about child's screen use",
                "Comfortable recording voice memos"
            ],
            "nice_to_have": [
                {"criterion": "Experience with Qualitative Research", "weight": 15},
                {"criterion": "Experience with Consumer Research", "weight": 15},
                {"criterion": "Detailed thoughtful proposal", "weight": 20}
            ],
            "red_flags": [
                "Generic proposal not mentioning kids/screens",
                "Says screens are not a concern"
            ]
        }
    },
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
    },
    
    # Parent / Qualitative Research Participants
    {
        "name": "Dinh P.",
        "title": "Management of Cross-Disciplinary Team, No scheduled weekend",
        "hourly_rate": 24.0,
        "job_success_score": 100,
        "total_earnings": 69.0,
        "top_rated_status": None,
        "skills": ["Management Skills", "Business Management", "Project Engineering", "IT Consultation"],
        "bio": "Highly motivated versatile Industrial Engineer and seasoned educator with 8+ years in industry and 4+ years in education. Dedicated to leverage my cross-disciplinary skills in business, education, and market research to create innovative solutions that leads to higher deal, client, and cash flow velocity.",
        "certifications": [],
        "portfolio": [],
        "work_history_summary": "Operations Manager | Droppii USA. Elementary school teacher | Korea International School. Entrepreneur in education | Home business.",
        "cover_letter_template": "Subject: Parent Desperately Seeking Solutions for Students' Phone Addiction\nHello. I’m reaching out because I'm dealing with a crisis that I believe your research is trying to address, and I need help understanding what works.\nI have kids ranging from 3 years old through 8th grade, and I'm watching screen addiction destroy their ability to focus, listen, and engage.\nDaily, my kids cannot accept \"no\" when it comes to their devices. When I tell them to put their phones away, they ignore me completely. I have to yell just to get any response, which is exhausting and creates an environment I hate. They're constantly watching TikTok, YouTube Shorts, and Instagram Reels. Their attention spans have collapsed.\nThe only method that works is physically removing the devices and putting them in a zipped bag.\nI'm watching my children develop dependency patterns. My middle school girl can't go a full period without experiencing withdrawal. I'm genuinely worried about the long-term damage to their brains, social skills, ability to delay gratification, and capacity for deep thinking.\nThis is an urgent crisis. My children are losing critical years of learning.\nI would be grateful for the opportunity to share my experiences through voice memos or calls. I have daily observations about what triggers the worst behaviors, what environmental factors help, and what I'm seeing across different age groups.\nThank you for working on solutions to this critical problem.\nBest regards,\nDinh Pham",
        "quality": "parent"
    },
    {
        "name": "Lucia D.",
        "title": "HR Information Systems Administrator",
        "hourly_rate": 30.0,
        "job_success_score": 100,
        "total_earnings": 200.0,
        "top_rated_status": None,
        "skills": ["Data Entry", "Company Research", "Market Research", "Project Management", "HR System Management", "Customer Care", "Budget Planning"],
        "bio": "I’m here to make your day easier by taking care of the details that keep your business running smoothly. I offer data entry, administrative support, and customer service with a focus on being thoughtful, dependable, and easy to work with. I know how much it matters to have someone who’s not just capable, but who genuinely cares about doing things right and supporting your goals.",
        "certifications": [],
        "portfolio": [],
        "work_history_summary": "HRIS Administrator | Superior Court of California. IT Project Manager | Superrior Court of California. Interim Client Services Manager | Alameda County Office of Education.",
        "cover_letter_template": "Hi there,\n\nI’m a parent of four kids under 18, and this is a topic that genuinely keeps me up at night.\n\nScreen time is a constant conversation in our house. While I’m a very involved parent and we do have boundaries and expectations, the reality is that managing phones, tablets, gaming, and internet use in today’s world is hard. It’s not something I’ve figured out once and moved on from, it’s something we’re actively navigating all the time.\n\nI’ve seen how screen use can impact mood, attention, sleep, focus, and overall family dynamics. I’ve tried different approaches over the years, setting limits, having ongoing conversations, adjusting rules as the kids grow. Some things have helped for a while, some haven’t worked at all, and sometimes what works for one child doesn’t work for another. It often feels like a moving target, especially as technology keeps changing.\n\nWhat I can offer is honest, real-world perspective. I’m very comfortable sharing openly through voice memos or calls about what’s been happening in our home, what’s worked and what hasn’t, and why this feels both urgent and emotionally heavy as a parent who truly cares about her kids’ well-being.\n\nThis isn’t just a mild frustration for me, it’s something I actively think about because I want to do right by my kids and help them build healthy habits in a very digital world.\n\nI’d be glad to contribute and also connect you with other parents who are facing similar challenges.\n\nThank you for the work you’re doing. I’d love to be part of it.\n\nBest,\nLucia Duong",
        "quality": "parent"
    }
]


def generate_mock_jobs(count: int = 10) -> List[JobCreate]:
    """Generate mock job postings."""
    jobs = []
    # Ensure count is at least 1 and doesn't exceed available templates excessively
    # We will cycle through templates if count > len(JOB_TEMPLATES)
    for i in range(count):
        template = JOB_TEMPLATES[i % len(JOB_TEMPLATES)]
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
    is_parent_job = "Parent" in job_title or "struggling" in job_title.lower()
    
    if is_parent_job:
        # For the parent job, mostly pick parent freelancers, but sometimes mix in a generic one (tier 3 / low quality)
        if random.random() < 0.7:
             freelancers = [f for f in FREELANCER_TEMPLATES if f["quality"] == "parent"]
        else:
             freelancers = [f for f in FREELANCER_TEMPLATES if f["quality"] == "low"]
    elif quality:
        freelancers = [f for f in FREELANCER_TEMPLATES if f["quality"] == quality]
    else:
        # Exclude parents from regular tech jobs usually
        freelancers = [f for f in FREELANCER_TEMPLATES if f["quality"] != "parent"]
    
    # Fallback if filtering resulted in empty list
    if not freelancers:
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
        work_history_summary=template.get("work_history_summary", "No history"),
        profile_url=f"https://upwork.com/freelancers/{freelancer_id}"
    )
    
    # Personalize cover letter based on template
    # Safe format using .get in case keys are missing or template is specialized
    try:
        cover_letter = template["cover_letter_template"].format(
            skill=random.choice(template["skills"]) if template["skills"] else "work",
            previous_client_type="tech startups" if template.get("quality") == "high" else "apps",
            specific_achievement="reducing API latency by 40%" if template.get("quality") == "high" else "share",
            reason="it aligns with my expertise" if template.get("quality") == "high" else "parents",
            relevant_skill=random.choice(template["skills"]) if template["skills"] else "feedback",
            achievement="5-star ratings on similar projects" if template.get("quality") == "high" else "several projects",
            project_goal="your goals" if template.get("quality") == "high" else "study",
            client_type="enterprise clients" if template.get("quality") == "high" else "researchers",
            result="significant cost savings" if template.get("quality") == "high" else "good insights"
        )
    except Exception:
        # Fallback for any format error
        cover_letter = f"Hi, I am interested in your project: {job_title}. I have experience and can help you. Please check my profile."
    
    # Bid amount varies based on hourly rate
    bid_amount = template["hourly_rate"] * random.randint(2, 5) # Lower hours for this gig
    
    return ProposalCreate(
        job_id=job_id,
        freelancer=freelancer,
        cover_letter=cover_letter,
        bid_amount=bid_amount,
        estimated_duration="1 week",
        screening_answers="I am available to start immediately."
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
