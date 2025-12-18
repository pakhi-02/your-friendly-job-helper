"""AI-powered job matching using OpenAI."""
from openai import OpenAI
from config import OPENAI_API_KEY, USER_PROFILE, MIN_MATCH_SCORE
import json


class AIJobMatcher:
    """Uses AI to match jobs with user profile."""
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.user_profile = USER_PROFILE
    
    def analyze_job(self, job_data):
        """
        Analyze a job posting and determine relevance.
        
        Args:
            job_data (dict): Job information including title, description, company, location
            
        Returns:
            dict: Analysis with score, reasoning, and recommendation
        """
        prompt = self._build_prompt(job_data)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert career counselor and job matcher. Analyze job postings and determine how well they match a candidate's profile."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
            
        except Exception as e:
            print(f"Error analyzing job: {e}")
            return {
                "match_score": 0,
                "reasoning": "Error analyzing job",
                "recommendation": "skip"
            }
    
    def _build_prompt(self, job_data):
        """Build the prompt for AI analysis."""
        return f"""
Analyze how well this job matches the candidate's profile.

**Candidate Profile:**
- Skills: {', '.join(self.user_profile['skills'])}
- Desired Roles: {', '.join(self.user_profile['desired_roles'])}
- Preferred Locations: {', '.join(self.user_profile['preferred_locations'])}
- Experience Level: {self.user_profile['experience_level']}

**Job Posting:**
- Title: {job_data.get('title', 'N/A')}
- Company: {job_data.get('company', 'N/A')}
- Location: {job_data.get('location', 'N/A')}
- Description: {job_data.get('description', 'N/A')[:1000]}

Provide your analysis in JSON format with:
1. "match_score": An integer from 0-100 indicating how well this job matches
2. "reasoning": A brief explanation (2-3 sentences) of why this score was given
3. "recommendation": Either "apply", "consider", or "skip"
4. "key_matches": A list of 2-3 key reasons this job matches (or doesn't)

Consider:
- Skills alignment
- Role suitability
- Location match
- Experience level fit
- Growth opportunities
"""
    
    def batch_analyze(self, jobs_list):
        """
        Analyze multiple jobs and return sorted by match score.
        
        Args:
            jobs_list (list): List of job dictionaries
            
        Returns:
            list: Jobs with analysis, sorted by match score
        """
        analyzed_jobs = []
        
        for idx, job in enumerate(jobs_list):
            print(f"Analyzing job {idx + 1}/{len(jobs_list)}: {job.get('title', 'Unknown')}")
            analysis = self.analyze_job(job)
            
            job['analysis'] = analysis
            job['match_score'] = analysis.get('match_score', 0)
            
            # Only include jobs above minimum threshold
            if job['match_score'] >= MIN_MATCH_SCORE:
                analyzed_jobs.append(job)
        
        # Sort by match score (highest first)
        analyzed_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return analyzed_jobs
