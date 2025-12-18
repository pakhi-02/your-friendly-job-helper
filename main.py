"""Main application for AI-powered job searching."""
import os
import json
import pandas as pd
from datetime import datetime
from config import USER_PROFILE, SEARCH_KEYWORDS
from ai_matcher import AIJobMatcher
from scrapers import get_all_scrapers


class JobSearcher:
    """Main job searcher application."""
    
    def __init__(self):
        self.matcher = AIJobMatcher()
        self.scrapers = get_all_scrapers()
        self.output_dir = "jobs_output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def search_all_jobs(self, keywords=None, max_per_keyword=30):
        """
        Search for jobs across all sources and keywords.
        
        Args:
            keywords (list): List of keywords to search. Uses config default if None.
            max_per_keyword (int): Maximum jobs to fetch per keyword
            
        Returns:
            list: All found jobs
        """
        if keywords is None:
            keywords = SEARCH_KEYWORDS
        
        all_jobs = []
        
        for keyword in keywords:
            print(f"\n{'='*60}")
            print(f"Searching for: {keyword}")
            print(f"{'='*60}")
            
            for scraper in self.scrapers:
                scraper_name = scraper.__class__.__name__
                print(f"\nUsing {scraper_name}...")
                
                try:
                    jobs = scraper.search_jobs(
                        keyword=keyword,
                        location="",
                        max_results=max_per_keyword
                    )
                    all_jobs.extend(jobs)
                    print(f"✓ Found {len(jobs)} jobs")
                    
                except Exception as e:
                    print(f"✗ Error with {scraper_name}: {e}")
        
        # Remove duplicates based on title and company
        unique_jobs = self._remove_duplicates(all_jobs)
        print(f"\n{'='*60}")
        print(f"Total unique jobs found: {len(unique_jobs)}")
        print(f"{'='*60}\n")
        
        return unique_jobs
    
    def _remove_duplicates(self, jobs):
        """Remove duplicate job postings."""
        seen = set()
        unique = []
        
        for job in jobs:
            key = (job.get('title', '').lower(), job.get('company', '').lower())
            if key not in seen:
                seen.add(key)
                unique.append(job)
        
        return unique
    
    def analyze_and_rank_jobs(self, jobs):
        """
        Analyze jobs using AI and rank by relevance.
        
        Args:
            jobs (list): List of job dictionaries
            
        Returns:
            list: Analyzed and ranked jobs
        """
        print("\n🤖 Analyzing jobs with AI...\n")
        return self.matcher.batch_analyze(jobs)
    
    def save_results(self, jobs, format='both'):
        """
        Save job search results to file.
        
        Args:
            jobs (list): List of analyzed jobs
            format (str): 'json', 'csv', or 'both'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format in ['json', 'both']:
            json_file = os.path.join(self.output_dir, f"jobs_{timestamp}.json")
            with open(json_file, 'w') as f:
                json.dump(jobs, f, indent=2)
            print(f"✓ Saved to: {json_file}")
        
        if format in ['csv', 'both']:
            csv_file = os.path.join(self.output_dir, f"jobs_{timestamp}.csv")
            df = self._jobs_to_dataframe(jobs)
            df.to_csv(csv_file, index=False)
            print(f"✓ Saved to: {csv_file}")
    
    def _jobs_to_dataframe(self, jobs):
        """Convert jobs list to pandas DataFrame."""
        rows = []
        for job in jobs:
            analysis = job.get('analysis', {})
            row = {
                'Match Score': job.get('match_score', 0),
                'Recommendation': analysis.get('recommendation', 'N/A'),
                'Title': job.get('title', 'N/A'),
                'Company': job.get('company', 'N/A'),
                'Location': job.get('location', 'N/A'),
                'Source': job.get('source', 'N/A'),
                'Link': job.get('link', 'N/A'),
                'Reasoning': analysis.get('reasoning', 'N/A'),
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def print_summary(self, jobs):
        """Print a summary of top job matches."""
        print("\n" + "="*80)
        print("🎯 TOP JOB MATCHES FOR YOU")
        print("="*80 + "\n")
        
        for idx, job in enumerate(jobs[:10], 1):  # Top 10
            analysis = job.get('analysis', {})
            print(f"{idx}. [{job.get('match_score', 0)}/100] {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Recommendation: {analysis.get('recommendation', 'N/A').upper()}")
            print(f"   Link: {job.get('link', 'N/A')}")
            print(f"   Why: {analysis.get('reasoning', 'N/A')}")
            print()
        
        print("="*80)
        print(f"Total matching jobs: {len(jobs)}")
        print("="*80 + "\n")
    
    def run(self):
        """Execute the full job search workflow."""
        print(f"\n👋 Hi {USER_PROFILE['name']}!")
        print(f"🔍 Searching for jobs matching your profile...\n")
        
        # Step 1: Search for jobs
        all_jobs = self.search_all_jobs()
        
        if not all_jobs:
            print("❌ No jobs found. Try adjusting your search keywords in config.py")
            return
        
        # Step 2: Analyze and rank with AI
        ranked_jobs = self.analyze_and_rank_jobs(all_jobs)
        
        if not ranked_jobs:
            print("❌ No jobs matched your criteria (score >= 70)")
            print("💡 Try lowering MIN_MATCH_SCORE in config.py")
            return
        
        # Step 3: Save results
        self.save_results(ranked_jobs)
        
        # Step 4: Print summary
        self.print_summary(ranked_jobs)
        
        print("✅ Job search complete!")


def main():
    """Main entry point."""
    searcher = JobSearcher()
    searcher.run()


if __name__ == "__main__":
    main()
