"""Simple job searcher without AI (no API costs)."""
import os
import json
import pandas as pd
from datetime import datetime
from config import USER_PROFILE, SEARCH_KEYWORDS
from scrapers import get_all_scrapers


class SimpleJobSearcher:
    """Simple job searcher without AI analysis."""
    
    def __init__(self):
        self.scrapers = get_all_scrapers()
        self.output_dir = "jobs_output"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def search_all_jobs(self, keywords=None, max_per_keyword=30):
        """Search for jobs across all sources and keywords."""
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
        
        # Remove duplicates
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
    
    def simple_filter(self, jobs):
        """Simple keyword-based filtering."""
        filtered = []
        user_skills = [s.lower().strip() for s in USER_PROFILE['skills']]
        user_roles = [r.lower().strip() for r in USER_PROFILE['desired_roles']]
        
        for job in jobs:
            title = job.get('title', '').lower()
            description = job.get('description', '').lower()
            combined_text = f"{title} {description}"
            
            # Simple scoring
            score = 0
            
            # Check if title matches desired roles
            for role in user_roles:
                if role in title:
                    score += 40
                    break
            
            # Check for skills in title or description
            skills_found = sum(1 for skill in user_skills if skill in combined_text)
            score += min(skills_found * 15, 60)
            
            job['simple_score'] = min(score, 100)
            
            if score >= 40:  # Lower threshold for simple matching
                filtered.append(job)
        
        # Sort by score
        filtered.sort(key=lambda x: x.get('simple_score', 0), reverse=True)
        return filtered
    
    def save_results(self, jobs, format='both'):
        """Save job search results to file."""
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
            row = {
                'Score': job.get('simple_score', 0),
                'Title': job.get('title', 'N/A'),
                'Company': job.get('company', 'N/A'),
                'Location': job.get('location', 'N/A'),
                'Source': job.get('source', 'N/A'),
                'Link': job.get('link', 'N/A'),
                'Description': job.get('description', 'N/A')[:200],
            }
            rows.append(row)
        
        return pd.DataFrame(rows)
    
    def print_summary(self, jobs):
        """Print a summary of top job matches."""
        print("\n" + "="*80)
        print("🎯 TOP JOB MATCHES FOR YOU (Simple Keyword Match)")
        print("="*80 + "\n")
        
        for idx, job in enumerate(jobs[:15], 1):  # Top 15
            print(f"{idx}. [{job.get('simple_score', 0)}/100] {job.get('title', 'N/A')}")
            print(f"   Company: {job.get('company', 'N/A')}")
            print(f"   Location: {job.get('location', 'N/A')}")
            print(f"   Source: {job.get('source', 'N/A')}")
            print(f"   Link: {job.get('link', 'N/A')}")
            print()
        
        print("="*80)
        print(f"Total matching jobs: {len(jobs)}")
        print("="*80 + "\n")
        print("💡 Tip: Add OpenAI credits for AI-powered matching with main.py")
    
    def run(self):
        """Execute the full job search workflow."""
        print(f"\n👋 Hi {USER_PROFILE['name']}!")
        print(f"🔍 Searching for jobs (Simple Mode - No AI costs)...\n")
        
        # Step 1: Search for jobs
        all_jobs = self.search_all_jobs()
        
        if not all_jobs:
            print("❌ No jobs found. Try adjusting your search keywords in config.py")
            return
        
        # Step 2: Simple filtering
        filtered_jobs = self.simple_filter(all_jobs)
        
        if not filtered_jobs:
            print("❌ No jobs matched your profile")
            return
        
        # Step 3: Save results
        self.save_results(filtered_jobs)
        
        # Step 4: Print summary
        self.print_summary(filtered_jobs)
        
        print("✅ Job search complete!")


def main():
    """Main entry point."""
    searcher = SimpleJobSearcher()
    searcher.run()


if __name__ == "__main__":
    main()
