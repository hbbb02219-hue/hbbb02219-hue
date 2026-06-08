"""
Anthropic Claude API integration
Resume aur banner content generate karta hai
"""

import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


async def generate_resume_content(
    name: str,
    job: str,
    skills: str,
    experience: str,
    style: str
) -> dict:
    """
    Claude API se professional resume content generate karta hai.
    Returns dict with: summary, keySkills, experience,
    education, linkedinHeadline, bannerTagline
    """
    prompt = f"""You are a professional resume writer. Generate resume content for:

Name: {name}
Job Title: {job}
Skills: {skills}
Experience: {experience}
Style preference: {style}

Return ONLY valid JSON (no markdown, no explanation) with this exact structure:
{{
  "summary": "2-3 line professional summary (Hindi-English mix ok)",
  "keySkills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "experience": [
    {{
      "company": "Company Name",
      "role": "Job Title",
      "duration": "X years",
      "achievement": "Key quantified achievement"
    }}
  ],
  "education": {{
    "degree": "Relevant degree",
    "college": "College/University name"
  }},
  "linkedinHeadline": "Catchy LinkedIn headline (max 10 words)",
  "bannerTagline": "Powerful banner tagline (max 8 words)"
}}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # Remove markdown fences if present
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)

    except json.JSONDecodeError:
        return _fallback_resume(name, job, skills, experience)
    except Exception as e:
        print(f"Claude API error: {e}")
        return _fallback_resume(name, job, skills, experience)


async def generate_banner_text(
    name: str,
    job: str,
    tagline: str
) -> str:
    """LinkedIn banner ke liye formatted Telegram message banata hai."""
    return (
        f"🖼️ *Aapka LinkedIn Banner:*\n"
        f"{'─' * 30}\n\n"
        f"👤 *{name}*\n"
        f"💼 {job}\n\n"
        f"✨ *\"{tagline}\"*\n\n"
        f"{'─' * 30}\n"
        f"📌 *Copy karo aur LinkedIn pe update karo!*\n\n"
        f"_Premium users ko high-quality PNG banner milta hai_ 🎨"
    )


def _fallback_resume(
    name: str,
    job: str,
    skills: str,
    experience: str
) -> dict:
    """API fail hone par fallback data."""
    skill_list = [s.strip() for s in skills.split(",")][:5]
    return {
        "summary": (
            f"{name} ek dedicated {job} hain jinka "
            f"{experience} ka strong background hai. "
            f"Naye challenges ke liye always ready rehte hain."
        ),
        "keySkills": skill_list,
        "experience": [
            {
                "company": "Previous Company",
                "role": job,
                "duration": experience,
                "achievement": (
                    "Team performance aur project delivery "
                    "mein significant contribution diya"
                ),
            }
        ],
        "education": {
            "degree": "Bachelor's Degree",
            "college": "University",
        },
        "linkedinHeadline": (
            f"{job} | "
            f"{skill_list[0] if skill_list else 'Professional'} Expert"
        ),
        "bannerTagline": "Building Excellence Every Day",
    }