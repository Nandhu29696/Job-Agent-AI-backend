import json
import ollama
from app.config import settings

client = ollama.AsyncClient(host=settings.ollama_base_url)

SYSTEM_PROMPT = """You are JobAgent AI, an expert career assistant. You help users:
- Find and evaluate job opportunities
- Write compelling cover letters tailored to job descriptions
- Review and improve resumes
- Prepare for interviews
- Analyze job-resume match scores with detailed feedback

Be concise, actionable, and encouraging. When generating cover letters, make them professional
and personalized. When analyzing matches, provide specific, constructive feedback."""


async def chat_with_agent(message: str, context: str | None = None) -> dict:
    """Send a message to the AI agent and get a response."""
    system = SYSTEM_PROMPT
    if context:
        system += f"\n\nCurrent context: {context}"

    response = await client.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
    )

    reply = response.message.content
    return {"reply": reply, "suggestions": []}


async def generate_cover_letter(
    job_title: str,
    company: str,
    job_description: str,
    resume_text: str,
    user_name: str,
) -> str:
    """Generate a tailored cover letter using AI."""
    prompt = f"""Write a professional cover letter for the following:

Position: {job_title} at {company}
Applicant: {user_name}

Job Description:
{job_description[:2000]}

Applicant's Resume/Background:
{resume_text[:2000]}

Write a compelling, concise cover letter (3-4 paragraphs) that:
1. Opens with a strong hook
2. Highlights relevant experience matching the job requirements
3. Shows enthusiasm for the company
4. Closes with a clear call to action

Return only the cover letter text."""

    response = await client.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": "You are an expert cover letter writer."},
            {"role": "user", "content": prompt},
        ],
    )
    return response.message.content


async def analyze_job_match(job_description: str, resume_text: str) -> dict:
    """Analyze how well a resume matches a job description."""
    prompt = f"""Analyze the match between this job description and resume.

Job Description:
{job_description[:2000]}

Resume:
{resume_text[:2000]}

Respond with a JSON object containing:
{{
  "score": <number 0-100>,
  "strengths": [<list of 3-5 matching strengths>],
  "gaps": [<list of 2-4 missing skills/experience>],
  "suggestions": [<list of 2-3 actionable improvements>]
}}

Return only valid JSON."""

    response = await client.chat(
        model=settings.ollama_model,
        messages=[
            {"role": "system", "content": "You are a professional recruiter and career coach."},
            {"role": "user", "content": prompt},
        ],
        format="json",
    )

    raw = response.message.content
    return json.loads(raw)
