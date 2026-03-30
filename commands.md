1. Start Ollama:
    ollama serve

2. Pull model (once):
  ollama pull llama3.2:3b

3. Run:
python main.py \
  --resume-file resume.pdf \
  --job-file job_description.docx \
  --company "Acme Inc" \
  --role "Software Engineer"