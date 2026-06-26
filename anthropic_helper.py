"""
Anthropic Claude API integration
Resume aur banner content generate karta hai
"""

import os
import json

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


async def generate_resume_content(
    name: str,
    job: str,
    skills: str,
    experience: str,
    style: str
) -> dict:
    import httpx

    prompt = f"""You are a professional resume writer. Generate resume content for:

Name: {name}
Job Title: {job}
Skills: {skills}
Experience: {experience}
Style preference: {style}

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
  "summary": "2-3 line professional summary",
  "keySkills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "X years",
      "achievement": "Key achievement"
    }}
  ],
  "education": {{
    "degree": "Relevant degree",
    "college": "College name"
  }},
  "linkedinHeadline": "Catchy LinkedIn headline max 10 words",
  "bannerTagline": "Powerful tagline max 8 words"
}}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            data = response.json()
            raw  = data["content"][0]["text"].strip()
            raw  = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(raw)

    except json.JSONDecodeError:
        return _fallback_resume(name, job, skills, experience)
    except Exception as e:
        print(f"API error: {e}")
        return _fallback_resume(name, job, skills, experience)


async def generate_banner_text(
    name: str,
    job: str,
    tagline: str
) -> str:
    return (
        f"🖼️ *Aapka LinkedIn Banner:*\n"
        f"{'─' * 30}\n\n"
        f"👤 *{name}*\n"
        f"💼 {job}\n\n"
        f"✨ *\"{tagline}\"*\n\n"
        f"{'─' * 30}\n"
        f"📌 *Copy karo aur LinkedIn pe update karo!*\n\n"
        f"_Premium users ko PNG banner milta hai_ 🎨"
    )


def _fallback_resume(
    name: str,
    job: str,
    skills: str,
    experience: str
) -> dict:
    skill_list = [s.strip() for s in skills.split(",")][:5]
    return {
        "summary": (
            f"{name} ek dedicated {job} hain jinka "
            f"{experience} ka strong background hai."
        ),
        "keySkills": skill_list,
        "experience": [{
            "company": "Previous Company",
            "role": job,
            "duration": experience,
            "achievement": "Team performance mein significant contribution",
        }],
        "education": {
            "degree": "Bachelor's Degree",
            "college": "University",
        },
        "linkedinHeadline": f"{job} | {skill_list[0] if skill_list else 'Professional'} Expert",
        "bannerTagline": "Building Excellence Every Day",
    }