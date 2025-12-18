"""Configuration settings for the AI Job Searcher."""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# User Profile
USER_PROFILE = {
    "name": os.getenv("YOUR_NAME", "Job Seeker"),
    "skills": os.getenv("YOUR_SKILLS", "").split(","),
    "desired_roles": os.getenv("DESIRED_ROLES", "").split(","),
    "preferred_locations": os.getenv("PREFERRED_LOCATIONS", "").split(","),
    "experience_level": os.getenv("EXPERIENCE_LEVEL", "Mid-Level")
}

# Job Search Configuration
SEARCH_KEYWORDS = [
    "software engineer",
    "data scientist",
    "machine learning engineer",
    "AI engineer"
]

# Scoring thresholds
MIN_MATCH_SCORE = 70  # Minimum score (0-100) to consider a job relevant
