"""Job scraper base class and implementations."""
from abc import ABC, abstractmethod
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class JobScraper(ABC):
    """Base class for job scrapers."""
    
    @abstractmethod
    def search_jobs(self, keyword, location="", max_results=50):
        """Search for jobs and return list of job dictionaries."""
        pass


class LinkedInScraper(JobScraper):
    """Scraper for LinkedIn job postings (note: requires login for full access)."""
    
    def search_jobs(self, keyword, location="", max_results=50):
        """Search LinkedIn jobs (simplified without login)."""
        jobs = []
        
        # LinkedIn public job search URL
        base_url = "https://www.linkedin.com/jobs/search"
        params = {
            "keywords": keyword,
            "location": location,
            "position": 1,
            "pageNum": 0
        }
        
        try:
            # Note: This is a simplified version. Full scraping requires handling pagination and anti-scraping measures
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(base_url, params=params, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # This is a placeholder - actual LinkedIn scraping is complex and may require Selenium
            print(f"LinkedIn search initiated for: {keyword} in {location}")
            print("Note: Full LinkedIn scraping requires authentication and advanced techniques")
            
        except Exception as e:
            print(f"Error scraping LinkedIn: {e}")
        
        return jobs


class IndeedScraper(JobScraper):
    """Scraper for Indeed job postings."""
    
    def search_jobs(self, keyword, location="", max_results=50):
        """Search Indeed for jobs."""
        jobs = []
        
        base_url = "https://www.indeed.com/jobs"
        params = {
            "q": keyword,
            "l": location,
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            
            response = requests.get(base_url, params=params, headers=headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors as Indeed changes frequently
            job_cards = (
                soup.find_all('div', class_='job_seen_beacon') or
                soup.find_all('div', {'data-testid': 'slider_item'}) or
                soup.find_all('div', class_='jobsearch-SerpJobCard') or
                soup.find_all('td', class_='resultContent')
            )
            
            for card in job_cards[:max_results]:
                try:
                    # Try multiple ways to extract title
                    title_elem = (
                        card.find('h2', class_='jobTitle') or
                        card.find('h2') or
                        card.find('a', class_='jcs-JobTitle')
                    )
                    
                    # Try multiple ways to extract company
                    company_elem = (
                        card.find('span', class_='companyName') or
                        card.find('span', {'data-testid': 'company-name'}) or
                        card.find('span', class_='company')
                    )
                    
                    # Try multiple ways to extract location
                    location_elem = (
                        card.find('div', class_='companyLocation') or
                        card.find('div', {'data-testid': 'text-location'}) or
                        card.find('span', class_='location')
                    )
                    
                    # Get snippet/description if available
                    snippet_elem = card.find('div', class_='job-snippet') or card.find('div', class_='summary')
                    
                    # Get job link
                    link_elem = title_elem.find('a') if title_elem else None
                    if not link_elem:
                        link_elem = card.find('a', href=True)
                    
                    job_id = link_elem.get('data-jk', '') if link_elem else ''
                    if not job_id and link_elem:
                        href = link_elem.get('href', '')
                        if 'jk=' in href:
                            job_id = href.split('jk=')[1].split('&')[0]
                    
                    if title_elem:  # Only add if we at least have a title
                        job = {
                            'title': title_elem.get_text(strip=True) if title_elem else 'N/A',
                            'company': company_elem.get_text(strip=True) if company_elem else 'N/A',
                            'location': location_elem.get_text(strip=True) if location_elem else 'Remote',
                            'link': f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else (link_elem.get('href', 'N/A') if link_elem else 'N/A'),
                            'source': 'Indeed',
                            'description': snippet_elem.get_text(strip=True) if snippet_elem else ''
                        }
                        jobs.append(job)
                    
                except Exception as e:
                    # Silently skip errors for individual cards
                    continue
            
            print(f"Found {len(jobs)} jobs on Indeed for: {keyword}")
            
        except Exception as e:
            print(f"Error scraping Indeed: {e}")
        
        return jobs


class RemoteOKScraper(JobScraper):
    """Scraper for RemoteOK remote jobs."""
    
    def search_jobs(self, keyword, location="", max_results=50):
        """Search RemoteOK for remote jobs."""
        jobs = []
        
        try:
            url = "https://remoteok.com/api"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            data = response.json()
            
            # First item is metadata, skip it
            job_listings = data[1:] if len(data) > 1 else []
            
            for job_data in job_listings[:max_results]:
                try:
                    # Filter by keyword
                    position = job_data.get('position', '').lower()
                    tags = ' '.join(job_data.get('tags', [])).lower()
                    
                    if keyword.lower() in position or keyword.lower() in tags:
                        job = {
                            'title': job_data.get('position', 'N/A'),
                            'company': job_data.get('company', 'N/A'),
                            'location': 'Remote',
                            'link': job_data.get('url', 'N/A'),
                            'source': 'RemoteOK',
                            'description': job_data.get('description', '')[:500]
                        }
                        jobs.append(job)
                        
                        if len(jobs) >= max_results:
                            break
                            
                except Exception as e:
                    print(f"Error parsing RemoteOK job: {e}")
                    continue
            
            print(f"Found {len(jobs)} jobs on RemoteOK for: {keyword}")
            
        except Exception as e:
            print(f"Error scraping RemoteOK: {e}")
        
        return jobs


class AdzunaScraper(JobScraper):
    """Sample scraper using mock data for demonstration."""
    
    def search_jobs(self, keyword, location="", max_results=50):
        """Return sample job data for demonstration."""
        jobs = []
        
        # This is sample/mock data to demonstrate the app functionality
        # In production, you would integrate with actual job APIs or scrape real sites
        sample_jobs = [
            {
                'title': f'Senior {keyword} - Remote',
                'company': 'TechCorp Inc',
                'location': 'Remote',
                'link': 'https://example.com/job1',
                'source': 'Sample Data',
                'description': f'We are looking for an experienced {keyword} to join our remote team. Must have 5+ years of experience with Python, cloud technologies, and agile methodologies.'
            },
            {
                'title': f'{keyword} - Hybrid',
                'company': 'StartupXYZ',
                'location': 'San Francisco, CA (Hybrid)',
                'link': 'https://example.com/job2',
                'source': 'Sample Data',
                'description': f'Join our innovative team as a {keyword}. Work on cutting-edge projects using modern tech stack. Competitive salary and benefits.'
            },
            {
                'title': f'Junior {keyword}',
                'company': 'DataDriven Co',
                'location': 'New York, NY',
                'link': 'https://example.com/job3',
                'source': 'Sample Data',
                'description': f'Entry-level {keyword} position. Great for recent graduates or career changers. We provide mentorship and training.'
            }
        ]
        
        jobs = sample_jobs[:max_results]
        print(f"Found {len(jobs)} sample jobs for: {keyword}")
        print("Note: These are sample jobs for demonstration. Integrate real job APIs for production use.")
        
        return jobs


def get_all_scrapers():
    """Return list of all available scrapers."""
    return [
        IndeedScraper(),
        AdzunaScraper(),  # Sample data scraper for demonstration
        # RemoteOKScraper(),  # Temporarily disabled due to API issues
        # LinkedInScraper(),  # Commented out as it needs more complex implementation
    ]
