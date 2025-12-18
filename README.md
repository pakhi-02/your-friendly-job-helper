# 🤖 AI-Powered Job Searcher

An intelligent job search tool that uses AI to find and rank job postings that match your skills and preferences. Get relevant job opportunities with direct application links!

## ✨ Features

- 🎯 **AI-Powered Matching**: Uses OpenAI GPT-4 to analyze jobs and match them to your profile
- 🌐 **Multiple Job Sources**: Scrapes from Indeed, RemoteOK, and more
- 📊 **Smart Ranking**: Jobs ranked by match score (0-100)
- 🔗 **Direct Apply Links**: Get direct links to job applications
- 💾 **Export Results**: Save results as JSON or CSV
- ⚙️ **Customizable**: Configure your skills, desired roles, and preferences

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository**:
   ```bash
   cd /Users/pakhichatterjee/ai-job-searcher/your_friendly_job_seaercher
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your settings**:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add:
   - Your OpenAI API key
   - Your name
   - Your skills (comma-separated)
   - Desired job roles
   - Preferred locations
   - Experience level

   Example:
   ```env
   OPENAI_API_KEY=sk-your-api-key-here
   YOUR_NAME=John Doe
   YOUR_SKILLS=Python,Machine Learning,AWS,Docker
   DESIRED_ROLES=ML Engineer,Data Scientist,Backend Engineer
   PREFERRED_LOCATIONS=Remote,San Francisco,New York
   EXPERIENCE_LEVEL=Mid-Level
   ```

### Usage

**Run the job searcher**:
```bash
python main.py
```

The app will:
1. Search for jobs across multiple platforms
2. Analyze each job using AI
3. Rank jobs by match score
4. Display top matches in the terminal
5. Save results to `jobs_output/` folder

### Output

Results are saved in the `jobs_output/` directory:
- **JSON format**: Full job details with AI analysis
- **CSV format**: Spreadsheet-friendly format for easy viewing

## 📁 Project Structure

```
your_friendly_job_seaercher/
├── main.py              # Main application entry point
├── ai_matcher.py        # AI-powered job matching logic
├── scrapers.py          # Job board scrapers
├── config.py            # Configuration settings
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your actual config (create this)
├── .gitignore          # Git ignore file
└── jobs_output/        # Output directory (auto-created)
```

## 🛠️ Customization

### Adjust Search Keywords

Edit `config.py` to modify search keywords:
```python
SEARCH_KEYWORDS = [
    "software engineer",
    "machine learning",
    "your custom keyword"
]
```

### Change Match Score Threshold

Lower this to see more jobs, raise it to be more selective:
```python
MIN_MATCH_SCORE = 70  # Jobs scoring below this are filtered out
```

### Add More Job Boards

Create a new scraper class in `scrapers.py`:
```python
class YourJobBoardScraper(JobScraper):
    def search_jobs(self, keyword, location="", max_results=50):
        # Your scraping logic here
        return jobs_list
```

## 📊 How It Works

1. **Scraping**: The app searches multiple job boards using your configured keywords
2. **Deduplication**: Removes duplicate postings
3. **AI Analysis**: Each job is analyzed by GPT-4 which:
   - Compares job requirements with your skills
   - Evaluates location and role fit
   - Generates a match score (0-100)
   - Provides reasoning for the score
   - Recommends: "apply", "consider", or "skip"
4. **Ranking**: Jobs are sorted by match score
5. **Output**: Top matches displayed and saved to files

## 🔒 Privacy & API Usage

- Your profile data stays local - only sent to OpenAI for job matching
- Each job analysis costs ~$0.001-0.002 (GPT-4 API pricing)
- For 50 jobs, expect ~$0.05-0.10 in API costs

## ⚠️ Important Notes

- **Rate Limiting**: Some job boards may block rapid requests. The app includes delays to be respectful.
- **Website Changes**: Job board HTML structures change frequently. Scrapers may need updates.
- **Authentication**: Some sites (like LinkedIn) require login for full access.
- **Legal**: Ensure your use complies with each website's Terms of Service.

## 🤝 Contributing

Feel free to:
- Add new job board scrapers
- Improve AI matching prompts
- Enhance the UI/output format
- Fix bugs or optimize code

## 📝 License

This project is for educational and personal use.

## 🆘 Troubleshooting

**No jobs found?**
- Check your internet connection
- Try different keywords in `config.py`
- Some job boards may block scrapers - this is expected

**API errors?**
- Verify your OpenAI API key in `.env`
- Check you have API credits available
- Ensure you're using a valid model (gpt-4 or gpt-3.5-turbo)

**Low match scores?**
- Adjust `MIN_MATCH_SCORE` in `config.py`
- Update your skills/preferences in `.env`
- Review the AI's reasoning to understand mismatches

## 🎯 Roadmap

- [ ] Add LinkedIn scraper with authentication
- [ ] Email notifications for new high-match jobs
- [ ] Web UI dashboard
- [ ] More job boards (Glassdoor, AngelList, etc.)
- [ ] Resume matching and tailoring suggestions
- [ ] Application tracking system

---

Happy job hunting! 🚀
