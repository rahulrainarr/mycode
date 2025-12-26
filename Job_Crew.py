import warnings
import os
import json
import re
from datetime import datetime, timedelta

warnings.filterwarnings('ignore')

from crewai import Agent, Task, Crew, Process
from crewai_tools import (
    FileReadTool,
    ScrapeWebsiteTool,
    MDXSearchTool,
    SerperDevTool
)
from langchain_openai import ChatOpenAI
# ============================================================================
# 1. IMPORT UTILS FIRST (This forces .env to load)
# ============================================================================
# By importing this here, the code inside utils.py runs immediately.
try:
    from utils import get_fast_llm, get_fast_llm, get_serper_key
    print("✅ Configuration loaded successfully from .env")
except Exception as e:
    print(f"❌ Error loading configuration: {e}")
    exit(1)

# ============================================================================
# 1. CONFIGURATION & API KEYS (FILL THESE IN)
# ============================================================================

# CRITICAL: Replace with your actual keys
# Get Serper Key here: https://serper.dev/api-key
#os.environ["SERPER_API_KEY"] = "YOUR_SERPER_API_KEY_HERE" 
# Get OpenAI Key here: https://platform.openai.com/api-keys
#os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY_HERE"

# Define LLMs
smart_llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
fast_llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# ============================================================================
# 2. TOOL INITIALIZATION
# ============================================================================

search_tool = SerperDevTool()
scrape_tool = ScrapeWebsiteTool()

RESUME_PATH = "D:\\01RAHUL\\12MyCode\\01Projects\\cv-RR.md"

if not os.path.exists(RESUME_PATH):
    print(f"ERROR: Resume file not found at {RESUME_PATH}")
    print("Please update the RESUME_PATH variable in the script.")
    exit(1)
else:
    read_resume = FileReadTool(file_path=RESUME_PATH)
    semantic_search_resume = MDXSearchTool(file_path=RESUME_PATH)

# ============================================================================
# 3. AGENTS
# ============================================================================job_scraper = Agent(
job_scraper = Agent(
    role="Job Search Specialist",
    goal="Find valid job links from Google Search results.",
    backstory=(
        "You are an expert internet researcher with a keen eye for detail. "
        "You know how to construct search queries that bypass spam and sponsored content. "
        "You are relentless in finding the specific URLs for job postings."
    ),
    tools=[search_tool, scrape_tool],
    llm=get_fast_llm(),
    max_iter=5,
    allow_delegation=False,
    verbose=True
)

profile_matcher = Agent(
    role="Profile Matcher",
    goal="Score jobs based on resume match.",
    backstory=(
        "You are a seasoned technical recruiter. When searching the resume, "
        "always use the 'search_query' parameter for your tool calls. "
        "You are critical and realistic; you don't give high scores unless the fit is genuine."
    ),
    tools=[read_resume, semantic_search_resume],
    llm=get_fast_llm(),
    max_iter=10,
    verbose=True
)

job_ranker = Agent(
    role="Job Ranker",
    goal="Select top jobs.",
    backstory=(
        "You are a career strategist and data analyst. "
        "You look beyond just the skills match to analyze company stability, "
        "growth potential, and alignment with the candidate's long-term goals."
    ),
    tools=[scrape_tool],
    llm=get_fast_llm(),
    max_iter=5,
    verbose=True
)

resume_strategist = Agent(
    role="Resume Writer",
    goal="Generate resume markdown content for top jobs.",
    backstory=(
        "You are an expert professional resume writer and ATS specialist. "
        "You know exactly how to phrase experiences to pass automated filters. "
        "You are a master at highlighting transferable skills without fabricating facts."
    ),
    tools=[read_resume, semantic_search_resume],
    llm=get_fast_llm(),
    max_iter=10,
    verbose=True
)

interview_prepper = Agent(
    role="Interview Coach",
    goal="Generate interview prep markdown content for top jobs.",
    backstory=(
        "You are a high-end interview coach for executives. "
        "You prepare candidates by analyzing the company's recent news, culture, "
        "and technical challenges to predict exactly what the interviewer will ask."
    ),
    tools=[scrape_tool, search_tool, read_resume],
    llm=get_fast_llm(),
    max_iter=5,
    verbose=True
)

# ============================================================================
# 4. TASKS (Updated for JSON Output)
# ============================================================================

job_search_task = Task(
    description=(
        "Search for jobs matching: {search_query} in {locations}.\n"
        "STRICT: Use the search_tool to find links. Then use scrape_tool to read the links.\n"
        "Return a JSON list of jobs with: title, company, url."
    ),
    expected_output="JSON array of job objects.",
    agent=job_scraper
)

profile_matching_task = Task(
    description=(
        "Match profile against jobs. {personal_writeup}\n"
        "Return a JSON array of jobs with added 'match_score' (0-100)."
    ),
    expected_output="JSON array with match scores.",
    agent=profile_matcher,
    context=[job_search_task]
)

job_ranking_task = Task(
    description=(
        "Rank jobs by score. Select top 10.\n"
        "Output a clean JSON list of the top 10 jobs."
    ),
    expected_output="JSON array of top 10 ranked jobs.",
    agent=job_ranker,
    context=[profile_matching_task],
    output_file="top_10_jobs.json", # This saves the raw ranking
    human_input=True
)

# UPDATED: Explicitly asks for a JSON map so we can save files later
resume_tailoring_task = Task(
    description=(
        "For the top 10 jobs provided, create a tailored resume content.\n"
        "CRITICAL OUTPUT FORMAT: You must output a single JSON object.\n"
        "The keys must be filenames (e.g., 'resume_Google_Engineer.md').\n"
        "The values must be the full markdown content of the resume.\n"
        "Do not output anything other than the JSON."
    ),
    expected_output="A JSON object mapping filenames to resume markdown content.",
    agent=resume_strategist,
    context=[job_ranking_task],
    output_file="resumes_data.json" 
)

# UPDATED: Explicitly asks for a JSON map
interview_prep_task = Task(
    description=(
        "For the top 10 jobs provided, create interview prep.\n"
        "CRITICAL OUTPUT FORMAT: You must output a single JSON object.\n"
        "The keys must be filenames (e.g., 'prep_Google_Engineer.md').\n"
        "The values must be the full markdown content of the interview guide.\n"
        "Do not output anything other than the JSON."
    ),
    expected_output="A JSON object mapping filenames to interview markdown content.",
    agent=interview_prepper,
    context=[job_ranking_task],
    output_file="interview_prep_data.json"
)

# ============================================================================
# 5. CREW EXECUTION
# ============================================================================

crew = Crew(
    agents=[job_scraper, profile_matcher, job_ranker, resume_strategist, interview_prepper],
    tasks=[job_search_task, profile_matching_task, job_ranking_task, resume_tailoring_task, interview_prep_task],
    process=Process.sequential,
    verbose=True
)

enhanced_inputs = {
    'search_query': 'Consultant AI Cloud Transformation Cybersecurity',
    'locations': ['Remote', 'Kuala Lumpur', 'Singapore'],
    'personal_writeup': """Rahul is a techno-commercial leader with 20+ years experience..."""
}

if __name__ == "__main__":
    print("Starting Crew...")
    
    try:
        # 1. Run the crew
        result = crew.kickoff(inputs=enhanced_inputs)
        print("\nCrew finished processing.")
        
        # 2. Custom File Generator Logic
        #    This reads the JSON files created by the tasks and splits them into individual files
        print("Saving individual files...")
        
        # Helper to clean and parse JSON (sometimes LLMs add text around the JSON)
        def extract_json(text):
            try:
                # Try finding first { and last }
                start = text.find('{')
                end = text.rfind('}') + 1
                if start != -1 and end != -1:
                    return json.loads(text[start:end])
                return json.loads(text)
            except:
                print(f"Error parsing JSON content. Check the output files manually.")
                return {}

        # Save Resumes
        if os.path.exists("resumes_data.json"):
            with open("resumes_data.json", "r", encoding='utf-8') as f:
                content = f.read()
                resumes = extract_json(content)
                
            # Create directory if not exists
            os.makedirs("tailored_resumes", exist_ok=True)
            
            for filename, body in resumes.items():
                # Clean filename just in case
                safe_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                if not safe_filename.endswith(".md"): safe_filename += ".md"
                
                filepath = os.path.join("tailored_resumes", safe_filename)
                with open(filepath, "w", encoding='utf-8') as f:
                    f.write(body)
                print(f"Saved: {filepath}")

        # Save Interview Prep
        if os.path.exists("interview_prep_data.json"):
            with open("interview_prep_data.json", "r", encoding='utf-8') as f:
                content = f.read()
                preps = extract_json(content)
            
            os.makedirs("interview_prep", exist_ok=True)
            
            for filename, body in preps.items():
                safe_filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                if not safe_filename.endswith(".md"): safe_filename += ".md"
                
                filepath = os.path.join("interview_prep", safe_filename)
                with open(filepath, "w", encoding='utf-8') as f:
                    f.write(body)
                print(f"Saved: {filepath}")
                
        print("\nAll Done!")
        print("Check 'tailored_resumes' and 'interview_prep' folders.")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()