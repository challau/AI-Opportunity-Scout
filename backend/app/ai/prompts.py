"""AI Agent prompts — centralized prompt management."""

SYSTEM_COORDINATOR = """You are an AI assistant for AI Opportunity Scout, a platform that helps students
discover hackathons, coding contests, internships, workshops, and developer events.

You help users find opportunities that match their interests, skills, and career goals.
You have access to a database of real, scraped events from platforms like Unstop, Devfolio,
HackerEarth, Devpost, Codeforces, Kaggle, and more.

When answering questions:
- Be helpful, concise, and specific
- Always suggest specific events when relevant
- Explain why you recommend certain opportunities
- Consider the user's profile and interests if available
"""

SUMMARIZER_PROMPT = """Summarize the following hackathon/event for students in 2-3 sentences.
Be concise and highlight: what it is, who it's for, prize/benefit, and deadline if available.

Event:
Title: {title}
Description: {description}
Platform: {platform}
Type: {event_type}
Prize: {prize}
Deadline: {deadline}
Eligibility: {eligibility}

Write a clear, exciting summary in 2-3 sentences:"""

RANKING_PROMPT = """Rate this opportunity for a student developer on a scale of 0-100.
Consider: relevance, prize value, prestige, learning opportunity, ease of participation.

Event: {title}
Type: {event_type}
Prize: {prize}
Platform: {platform}
Eligibility: {eligibility}

Return JSON: {{"score": <0-100>, "reason": "<brief explanation>"}}"""

DUPLICATE_DETECTION_PROMPT = """Are these two events the same opportunity?
Compare titles, platforms, dates, and descriptions.

Event 1: {event1}
Event 2: {event2}

Return JSON: {{"is_duplicate": <true/false>, "confidence": <0-1>, "reason": "<brief>"}}"""

RESUME_MATCH_PROMPT = """Analyze how well this resume matches the given opportunity.

Resume Skills: {skills}
Resume Text Summary: {resume_summary}

Opportunity: {event_title}
Type: {event_type}
Requirements: {eligibility}
Tags: {tags}

Return JSON:
{{
  "match_percentage": <0-100>,
  "matching_skills": ["skill1", "skill2"],
  "explanation": "<2-3 sentences explaining the match>"
}}"""

EMAIL_TEMPLATE_PROMPT = """Generate a beautiful, professional HTML email for this opportunity notification.

User: {user_name}
Event: {event_title}
Platform: {platform}
Type: {event_type}
Prize: {prize}
Deadline: {deadline}
Summary: {summary}
Registration URL: {registration_url}
AI Recommendation Reason: {ai_reason}

Generate a complete, responsive HTML email with:
- Modern gradient header
- Clear event details
- CTA button for registration
- Why we recommend it section
- Clean footer
"""

CHATBOT_SYSTEM = """You are an intelligent AI assistant for AI Opportunity Scout.
Help students discover hackathons, internships, coding contests, and developer events.

Current user profile:
{user_profile}

Available events in our database: {event_count} events across 15+ platforms.

You can help users:
- Find events matching their interests
- Understand event requirements  
- Compare different opportunities
- Plan their participation schedule

When suggesting events, format them clearly with title, platform, deadline, and prize.
Always be encouraging and helpful."""

NORMALIZER_PROMPT = """Normalize this raw event data into our standard format.

Raw data: {raw_data}

Return a JSON object with these fields (use null for missing):
{{
  "title": "string",
  "description": "string",
  "platform": "string",
  "event_type": "hackathon|contest|internship|workshop|competition|quiz|open_source|hiring|conference",
  "prize": "string or null",
  "prize_amount": "number or null (USD equivalent)",
  "deadline": "ISO datetime or null",
  "event_start_date": "ISO datetime or null",
  "location": "string or null",
  "is_remote": "boolean",
  "is_free": "boolean",
  "eligibility": "string or null",
  "tags": ["array", "of", "strings"],
  "domains": ["AI/ML", "Web Dev", etc],
  "registration_url": "string"
}}"""
