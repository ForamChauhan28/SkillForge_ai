import os
import json
import time
from google import genai
from google.genai import types
from config import Config

client = None

# Ordered model fallback chain — if one fails, try the next
MODEL_CHAIN = [
    'gemini-3.6-flash',          # Latest fast and capable
    'gemini-3.5-flash',          # Previous gen fallback
    'gemini-3.5-flash-lite',     # Cost-efficient fallback
]

def get_client():
    global client
    if client is None:
        client = genai.Client(api_key=Config.GEMINI_API_KEY)
    return client


def _call_gemini(prompt, temperature=0.7, max_retries=3):
    """Helper to call Gemini API with retry logic and model fallback.
    
    Handles:
    - 429 (quota exhausted): skip to next model (each has its own quota)
    - 503 (overloaded): retry with exponential backoff
    - 404 (deprecated): skip to next model
    """
    last_error = None

    for model_name in MODEL_CHAIN:
        for attempt in range(max_retries):
            try:
                response = get_client().models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json',
                        temperature=temperature,
                    )
                )
                return json.loads(response.text)
            except Exception as e:
                last_error = e
                err_str = str(e)
                # 429 = quota exhausted for this model, skip to next model
                if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                    print(f"[AI] {model_name} quota exhausted, trying next model...")
                    break  # break inner loop, move to next model
                # 503 = overloaded, retry with backoff
                elif '503' in err_str:
                    wait = (attempt + 1) * 2  # 2s, 4s, 6s
                    print(f"[AI] {model_name} overloaded (attempt {attempt+1}/{max_retries}), retrying in {wait}s...")
                    time.sleep(wait)
                    continue
                # 404 = model deprecated, skip to next model
                elif '404' in err_str:
                    print(f"[AI] {model_name} not available, trying next model...")
                    break
                # Other errors: raise immediately
                else:
                    print(f"[AI] {model_name} error: {e}")
                    raise

    # All models and retries exhausted
    raise last_error or Exception("All Gemini models failed. Please try again later.")



# ═══════════════════════════════════════════════════
#  Resume & Skills
# ═══════════════════════════════════════════════════

def extract_skills(resume_text):
    """Extract categorized skills from resume text."""
    prompt = (
        'You are an expert technical recruiter. Read the following resume text and extract the candidate\'s '
        'core technical skills, programming languages, frameworks, tools, and soft skills. '
        'Output the result strictly as a JSON object: '
        '{"technical_skills": [...], "languages": [...], "frameworks": [...], "tools": [...], "soft_skills": [...]}'
        f'\n\nResume Text:\n{resume_text}'
    )
    try:
        return _call_gemini(prompt, temperature=0.1)
    except Exception as e:
        print(f"Error extracting skills: {e}")
        return None


def score_resume_ats(resume_text, dream_job=""):
    """Score a resume against ATS best practices. Returns score breakdown."""
    job_context = f' for a {dream_job} role' if dream_job else ''
    prompt = (
        f'You are an expert ATS (Applicant Tracking System) analyzer. Score this resume{job_context} '
        f'on a scale of 0-100. Break down the score into 5 categories, each scored 0-20:\n'
        f'1. format_structure: Resume formatting, section organization, length\n'
        f'2. keyword_optimization: Relevant industry keywords and buzzwords\n'
        f'3. skills_match: Technical and soft skills alignment{" with " + dream_job if dream_job else ""}\n'
        f'4. impact_statements: Use of quantified achievements, action verbs\n'
        f'5. readability: Clear writing, proper grammar, professional tone\n\n'
        f'Also provide 3-5 specific, actionable improvement suggestions.\n\n'
        f'Output as JSON: {{"overall_score": N, "categories": {{"format_structure": N, '
        f'"keyword_optimization": N, "skills_match": N, "impact_statements": N, '
        f'"readability": N}}, "suggestions": ["...", "..."], '
        f'"summary": "One sentence overall assessment"}}\n\n'
        f'Resume Text:\n{resume_text}'
    )
    try:
        return _call_gemini(prompt, temperature=0.2)
    except Exception as e:
        print(f"Error scoring resume: {e}")
        return None


# ═══════════════════════════════════════════════════
#  Roadmap Generation (Enhanced Schema)
# ═══════════════════════════════════════════════════

def generate_roadmap(extracted_skills, dream_job):
    """Generate a comprehensive learning roadmap using chained LLM calls."""
    try:
        # Call 1 - Industry Profiling
        prompt1 = (
            f'For the role of {dream_job}, list all required technical skills, tools, frameworks, '
            f'and knowledge areas that a professional needs. Output as JSON: {{"required_skills": [...]}}'
        )
        required_skills = _call_gemini(prompt1).get('required_skills', [])

        # Call 2 - Gap Analysis
        prompt2 = (
            f'Compare these CURRENT skills: {json.dumps(extracted_skills)} with these REQUIRED skills '
            f'for a {dream_job}: {json.dumps(required_skills)}. Identify the MISSING skills and also list which '
            f'existing skills are relevant. Output as JSON: {{"missing_skills": [...], "existing_relevant": [...]}}'
        )
        gap_analysis = _call_gemini(prompt2)
        missing_skills = gap_analysis.get('missing_skills', [])
        existing_relevant = gap_analysis.get('existing_relevant', [])

        # Call 3 - Enhanced Roadmap with spine/node/drawer structure
        prompt3 = (
            f'You are an expert curriculum designer. Create a comprehensive, visually structured learning roadmap '
            f'for someone who needs to learn these missing skills: {json.dumps(missing_skills)} to become a {dream_job}. '
            f'They already know: {json.dumps(existing_relevant)}.\n\n'
            f'The roadmap should have:\n'
            f'1. A sequential SPINE (main learning path) organized into phases\n'
            f'2. Each topic node must have a STATUS: "recommended" (core required), "alternative" (valid option), or "flexible" (good to know)\n'
            f'3. Each topic must include drawer_content with a definition, subtopics list, and free_resources\n\n'
            f'Output as strict JSON:\n'
            f'{{"roadmap": {{'
            f'"goal": "{dream_job}", '
            f'"estimated_weeks": N, '
            f'"milestones": [{{"after_phase": 1, "title": "...", "description": "..."}}], '
            f'"phases": [{{'
            f'"phase_id": 1, '
            f'"title": "...", '
            f'"duration_weeks": N, '
            f'"description": "One sentence phase summary", '
            f'"topics": [{{'
            f'"name": "...", '
            f'"description": "...", '
            f'"status": "recommended|alternative|flexible", '
            f'"priority": "high|medium|low", '
            f'"parent_topic": null, '
            f'"drawer_content": {{'
            f'"definition": "2-3 sentence technical definition", '
            f'"subtopics": ["...", "..."], '
            f'"free_resources": [{{"title": "...", "url": "...", "type": "Video|Article|Course|Documentation"}}]'
            f'}}'
            f'}}]'
            f'}}]'
            f'}}}}'
        )
        return _call_gemini(prompt3)
    except Exception as e:
        print(f"Error generating roadmap: {e}")
        raise Exception(f"Roadmap generation failed: {e}")


# ═══════════════════════════════════════════════════
#  Certifications, Projects, Interview
# ═══════════════════════════════════════════════════

def generate_certifications(roadmap_json, dream_job):
    """Generate certification recommendations."""
    prompt = (
        f'Based on this learning roadmap for becoming a {dream_job}: {json.dumps(roadmap_json)}, '
        f'suggest 5-7 industry-recognized certifications. For each include: name, issuing_body, '
        f'estimated_cost (string like "$200" or "Free"), difficulty (beginner/intermediate/advanced), '
        f'duration (e.g. "4 weeks"), description (one sentence), and a url to the certification page. '
        f'Output as JSON: {{"certifications": [...]}}'
    )
    try:
        return _call_gemini(prompt)
    except Exception as e:
        print(f"Error generating certifications: {e}")
        return None


def generate_projects(extracted_skills, dream_job):
    """Generate tiered portfolio project suggestions."""
    prompt = (
        f'Generate 5 portfolio projects for someone learning to become a {dream_job}. '
        f'Their current skills include: {json.dumps(extracted_skills)}. '
        f'Categorize into tiers: Beginner (2 projects, focus on fundamentals), '
        f'Intermediate (2 projects, combines multiple concepts), Advanced (1 capstone project, resume-worthy). '
        f'For each project include: title, tier, description, tech_stack (list), learning_outcomes (list), '
        f'estimated_hours (number), prerequisites (list). Output as JSON: {{"projects": [...]}}'
    )
    try:
        return _call_gemini(prompt)
    except Exception as e:
        print(f"Error generating projects: {e}")
        return None


def generate_interview_prep(dream_job):
    """Generate interview preparation Q&A."""
    prompt = (
        f'Generate comprehensive interview preparation for a {dream_job} role. Include: '
        f'7 technical questions with detailed model answers, 3 behavioral questions with STAR-method '
        f'example answers. For each include: type (technical/behavioral), difficulty (easy/medium/hard), '
        f'question, answer, key_points (list of 2-3 key takeaways). '
        f'Output as JSON: {{"questions": [...]}}'
    )
    try:
        return _call_gemini(prompt)
    except Exception as e:
        print(f"Error generating interview prep: {e}")
        return None


# ═══════════════════════════════════════════════════
#  Skill Gap Analysis (for Radar Chart)
# ═══════════════════════════════════════════════════

def generate_skill_gap_analysis(current_skills, dream_job):
    """Generate numerical skill ratings for radar chart visualization."""
    prompt = (
        f'You are a career assessment expert. For someone aiming to become a {dream_job}, '
        f'their current skills are: {current_skills}.\n\n'
        f'Rate their proficiency in 8 key competency areas on a scale of 1-10, '
        f'and also provide the required level (1-10) for each area for a {dream_job}.\n\n'
        f'The 8 areas should be relevant to {dream_job} (e.g., for a developer: '
        f'Frontend, Backend, Databases, DevOps, System Design, DSA, Soft Skills, Domain Knowledge).\n\n'
        f'Output as JSON: {{"categories": ["Cat1", "Cat2", ...], '
        f'"current_levels": [N, N, ...], "required_levels": [N, N, ...], '
        f'"gap_summary": "Brief overall assessment"}}'
    )
    try:
        return _call_gemini(prompt, temperature=0.3)
    except Exception as e:
        print(f"Error generating skill gap analysis: {e}")
        return None


# ═══════════════════════════════════════════════════
#  AI Career Mentor Chat
# ═══════════════════════════════════════════════════

def chat_with_mentor(user_message, context):
    """Chat with AI career mentor. Context includes user profile data."""
    skills = context.get('skills', 'Not provided')
    dream_job = context.get('dream_job', 'Not specified')
    progress = context.get('progress', 'No roadmap yet')
    chat_history = context.get('history', [])

    # Build conversation history
    history_text = ""
    for msg in chat_history[-6:]:  # Last 6 messages for context window
        role = "Student" if msg.get('role') == 'user' else "Mentor"
        history_text += f"{role}: {msg.get('content', '')}\n"

    system_context = (
        f'You are SkillForge AI Mentor, an expert career counselor and technical mentor. '
        f'You are warm, encouraging, and specific in your advice.\n\n'
        f'--- STUDENT PROFILE ---\n'
        f'Current Skills: {skills}\n'
        f'Dream Job: {dream_job}\n'
        f'Learning Progress: {progress}\n'
        f'--- END PROFILE ---\n\n'
        f'Rules:\n'
        f'- Give specific, actionable advice based on their profile\n'
        f'- Reference their actual skills and dream job in your answers\n'
        f'- Be encouraging but realistic\n'
        f'- Use markdown formatting for readability (bold, bullet points, headers)\n'
        f'- Keep responses concise (2-4 paragraphs max)\n'
        f'- If asked about interview prep, give actual practice questions\n'
        f'- If asked about projects, suggest specific ones with tech stacks\n\n'
    )

    if history_text:
        system_context += f'--- CONVERSATION HISTORY ---\n{history_text}--- END HISTORY ---\n\n'

    prompt = system_context + f'Student: {user_message}\n\nMentor:'

    try:
        last_error = None
        for model_name in MODEL_CHAIN:
            for attempt in range(3):
                try:
                    response = get_client().models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            temperature=0.7,
                        )
                    )
                    return response.text
                except Exception as e:
                    last_error = e
                    err_str = str(e)
                    if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                        print(f"[AI Chat] {model_name} quota exhausted, trying next model...")
                        break
                    elif '503' in err_str:
                        time.sleep((attempt + 1) * 2)
                        continue
                    elif '404' in err_str:
                        break
                    else:
                        raise
        raise last_error or Exception("All models failed")
    except Exception as e:
        print(f"Error in mentor chat: {e}")
        return "I'm sorry, I encountered an issue. Please try again in a moment."


def chat_about_topic(topic, user_message, context):
    """Chat specifically about a roadmap topic."""
    skills = context.get('skills', 'Not provided')
    dream_job = context.get('dream_job', 'Not specified')

    system_context = (
        f'You are SkillForge AI Tutor, an expert technical instructor.\n'
        f'You are currently tutoring a student who is learning to become a {dream_job}.\n'
        f'The student is asking a question about the topic: "{topic}".\n\n'
        f'Rules:\n'
        f'- Keep your answer highly focused on "{topic}".\n'
        f'- Explain concepts simply and clearly, using analogies if helpful.\n'
        f'- Keep responses concise (1-3 paragraphs max).\n'
        f'- Use markdown formatting for readability (bolding key terms).\n'
        f'- If they ask for code, provide a very brief, practical code snippet.\n\n'
    )

    prompt = system_context + f'Student: {user_message}\n\nTutor:'

    try:
        last_error = None
        for attempt in range(3):
            try:
                response = get_client().models.generate_content(
                    model='gemini-3.5-flash-lite',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.4,
                    )
                )
                return response.text
            except Exception as e:
                last_error = e
                err_str = str(e)
                if '429' in err_str or 'RESOURCE_EXHAUSTED' in err_str:
                    break
                elif '503' in err_str:
                    time.sleep((attempt + 1) * 2)
                    continue
                elif '404' in err_str:
                    break
                else:
                    raise
        raise last_error or Exception("Model failed")
    except Exception as e:
        print(f"Error in topic chat: {e}")
        return "I'm sorry, I encountered an issue while thinking. Please try again."


# ═══════════════════════════════════════════════════
#  AI Mock Interview Simulator
# ═══════════════════════════════════════════════════

def generate_mock_questions(role, company, round_type, user_skills='', num_questions=5):
    """Generate a set of interview questions for a mock interview session."""
    round_descriptions = {
        'technical_r1': 'Technical Round 1 (core fundamentals, problem-solving, coding concepts)',
        'technical_r2': 'Technical Round 2 (system design, architecture, deep-dive)',
        'hr_behavioral': 'HR Behavioral Round (culture fit, teamwork, leadership, conflict resolution)',
        'mixed': 'Mixed Round (combination of technical and behavioral questions)',
    }
    round_desc = round_descriptions.get(round_type, round_type)
    
    company_context = f' at {company}' if company and company != 'General' else ''
    skills_context = f'\nCandidate\'s current skills: {user_skills}' if user_skills else ''
    
    prompt = (
        f'You are a senior interviewer conducting a {round_desc} for a {role} position{company_context}.\n'
        f'{skills_context}\n\n'
        f'Generate exactly {num_questions} interview questions. Each question should be realistic, '
        f'progressively challenging, and appropriate for the round type.\n\n'
        f'For Technical rounds: include coding concepts, problem-solving, system design based on difficulty.\n'
        f'For HR/Behavioral rounds: include questions that test STAR method responses (Situation, Task, Action, Result).\n'
        f'For Mixed rounds: include a blend of both.\n\n'
        f'Output as JSON:\n'
        f'{{"questions": [{{\n'
        f'  "question": "The interview question text",\n'
        f'  "category": "technical|behavioral|situational",\n'
        f'  "difficulty": "easy|medium|hard",\n'
        f'  "expected_topics": ["key topic 1", "key topic 2", "key topic 3"],\n'
        f'  "time_limit_seconds": 120\n'
        f'}}]}}'
    )
    try:
        result = _call_gemini(prompt, temperature=0.7)
        return result.get('questions', [])
    except Exception as e:
        print(f"Error generating mock questions: {e}")
        return []


def evaluate_mock_answer(question, user_answer, category, round_type, role, previous_qa=None):
    """Evaluate a candidate's answer to a mock interview question."""
    if not user_answer or not user_answer.strip() or user_answer.strip().lower() == "i would like to skip this question.":
        return {
            'overall_score': 0.0,
            'criteria_scores': {},
            'strengths': [],
            'improvements': ['No answer provided.'],
            'missing_points': ['The entire answer is missing.'],
            'model_answer': 'No answer was provided to evaluate.',
            'tip': 'Even if you are unsure, try to talk through your thought process.'
        }

    prev_context = ''
    if previous_qa:
        prev_context = '\n--- Previous Q&A Context ---\n'
        for qa in previous_qa[-3:]:
            prev_context += f"Q: {qa.get('question', '')}\nA: {qa.get('answer', '')}\n\n"
    
    if category == 'behavioral' or round_type == 'hr_behavioral':
        eval_criteria = (
            'Evaluate this answer using the STAR method framework:\n'
            '- Situation: Did the candidate describe the context clearly? (0-10)\n'
            '- Task: Did they explain their specific responsibility? (0-10)\n'
            '- Action: Did they detail the steps they took? (0-10)\n'
            '- Result: Did they share the outcome with measurable impact? (0-10)\n'
            '- Clarity: Was the answer well-structured and concise? (0-10)\n'
        )
    else:
        eval_criteria = (
            'Evaluate this answer on the following criteria:\n'
            '- Technical Accuracy: Are the concepts and facts correct? (0-10)\n'
            '- Depth: Does the answer show deep understanding? (0-10)\n'
            '- Problem Solving: Does it demonstrate logical thinking? (0-10)\n'
            '- Communication: Is the answer clear and well-structured? (0-10)\n'
            '- Completeness: Does it cover all key aspects? (0-10)\n'
        )
    
    prompt = (
        f'You are a senior {role} interviewer evaluating a candidate\'s response.\n\n'
        f'{prev_context}'
        f'--- Current Question ---\n'
        f'Question: {question}\n\n'
        f'--- Candidate\'s Answer ---\n'
        f'{user_answer}\n\n'
        f'--- Evaluation Criteria ---\n'
        f'{eval_criteria}\n'
        f'Provide constructive, encouraging feedback. Be specific about what was good and what could be improved.\n\n'
        f'Output as JSON:\n'
        f'{{\n'
        f'  "overall_score": 7.5,\n'
        f'  "criteria_scores": {{"criterion_name": score, ...}},\n'
        f'  "strengths": ["specific strength 1", "specific strength 2"],\n'
        f'  "improvements": ["specific area to improve 1", "specific area to improve 2"],\n'
        f'  "missing_points": ["key point the candidate missed"],\n'
        f'  "model_answer": "A concise, ideal answer to this question that the candidate can learn from",\n'
        f'  "tip": "One actionable tip for improving this type of answer"\n'
        f'}}'
    )
    try:
        result = _call_gemini(prompt, temperature=0.3)
        return result
    except Exception as e:
        print(f"Error evaluating mock answer: {e}")
        return {
            'overall_score': 0.0,
            'criteria_scores': {},
            'strengths': [],
            'improvements': ['Could not evaluate - please try again'],
            'missing_points': [],
            'model_answer': 'Evaluation failed. Please try again.',
            'tip': 'Try to be specific and structured in your answers.'
        }


def generate_mock_interview_report(role, round_type, company, qna_list):
    """Generate a comprehensive post-interview performance report."""
    # Build Q&A summary
    qa_summary = ''
    for i, qa in enumerate(qna_list, 1):
        qa_summary += (
            f'\nQ{i} [{qa.get("category", "general")}] ({qa.get("difficulty", "medium")}): {qa.get("question", "")}\n'
            f'Candidate Answer: {qa.get("user_answer", "No answer")}\n'
            f'Score: {qa.get("score", "N/A")}/10\n'
        )
    
    company_ctx = f' at {company}' if company and company != 'General' else ''
    
    prompt = (
        f'You are a career coach reviewing a mock interview performance.\n\n'
        f'Role: {role}{company_ctx}\n'
        f'Round Type: {round_type}\n\n'
        f'--- Interview Q&A Performance ---\n'
        f'{qa_summary}\n\n'
        f'Generate a comprehensive post-interview performance report.\n\n'
        f'Output as JSON:\n'
        f'{{\n'
        f'  "overall_score": 7.5,\n'
        f'  "overall_grade": "B+",\n'
        f'  "summary": "2-3 sentence overall assessment",\n'
        f'  "category_scores": {{\n'
        f'    "communication": 8.0,\n'
        f'    "technical_knowledge": 7.0,\n'
        f'    "problem_solving": 7.5,\n'
        f'    "confidence": 6.5,\n'
        f'    "structure": 7.0\n'
        f'  }},\n'
        f'  "top_strengths": ["strength 1", "strength 2", "strength 3"],\n'
        f'  "areas_to_improve": ["area 1", "area 2", "area 3"],\n'
        f'  "action_plan": [\n'
        f'    {{"action": "Specific action to take", "priority": "high|medium|low", "timeframe": "This week"}}\n'
        f'  ],\n'
        f'  "verdict": "HIRE|LEAN_HIRE|LEAN_NO_HIRE|NO_HIRE",\n'
        f'  "encouragement": "A motivating closing message for the candidate"\n'
        f'}}'
    )
    try:
        result = _call_gemini(prompt, temperature=0.4)
        return result
    except Exception as e:
        print(f"Error generating interview report: {e}")
        return {
            'overall_score': 0,
            'overall_grade': 'N/A',
            'summary': 'Report generation failed. Please try again.',
            'top_strengths': [],
            'areas_to_improve': [],
            'action_plan': [],
            'verdict': 'N/A',
            'encouragement': 'Keep practicing! Every interview is a learning opportunity.'
        }


# ═══════════════════════════════════════════════════
#  Landing Page Data
# ═══════════════════════════════════════════════════

def get_trending_roles():
    """Return static trending job roles for the landing page."""
    return [
        {"title": "Full Stack Developer", "icon": "code", "growth": "+25%", "avg_salary": "$95K"},
        {"title": "Data Scientist", "icon": "chart", "growth": "+36%", "avg_salary": "$120K"},
        {"title": "Cloud Engineer", "icon": "cloud", "growth": "+30%", "avg_salary": "$115K"},
        {"title": "AI/ML Engineer", "icon": "brain", "growth": "+40%", "avg_salary": "$130K"},
        {"title": "DevOps Engineer", "icon": "settings", "growth": "+28%", "avg_salary": "$110K"},
        {"title": "Cybersecurity Analyst", "icon": "shield", "growth": "+32%", "avg_salary": "$105K"},
    ]

def get_demo_roadmaps():
    """Return sample roadmap previews for the landing page."""
    return [
        {
            "slug": "full-stack-developer",
            "icon": "⚡",
            "title": "Full Stack Developer",
            "phases": ["Frontend", "Backend", "Database", "DevOps", "Projects"],
            "weeks": 16,
            "topics_count": 25,
        },
        {
            "slug": "data-scientist",
            "icon": "📊",
            "title": "Data Scientist",
            "phases": ["Python & Stats", "Data Analysis", "Machine Learning", "Deep Learning"],
            "weeks": 20,
            "topics_count": 30,
        },
        {
            "slug": "backend-developer",
            "icon": "🔧",
            "title": "Backend Developer",
            "phases": ["Programming", "Databases", "APIs & Auth", "System Design", "DevOps"],
            "weeks": 18,
            "topics_count": 28,
        },
    ]


def get_demo_roadmap_detail(slug):
    """Return a full detailed roadmap for public demo viewing (no AI call needed)."""
    roadmaps = {
        "full-stack-developer": {
            "goal": "Full Stack Developer",
            "icon": "⚡",
            "estimated_weeks": 16,
            "description": "A comprehensive path from frontend fundamentals to full-stack mastery, covering React, Node.js, databases, and deployment.",
            "phases": [
                {
                    "phase_id": 1, "title": "Frontend Foundations", "duration_weeks": 3,
                    "description": "Master the building blocks of the web.",
                    "topics": [
                        {"name": "HTML5 & Semantic Markup", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "HTML5 provides the structural foundation for all web pages. Semantic elements like <article>, <nav>, and <section> improve accessibility and SEO.",
                                           "subtopics": ["Forms & validation", "Accessibility (a11y)", "SEO best practices", "HTML5 APIs"],
                                           "free_resources": [{"title": "MDN HTML Guide", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML", "type": "Documentation"},
                                                              {"title": "freeCodeCamp HTML", "url": "https://www.freecodecamp.org/learn/responsive-web-design/", "type": "Course"}]}},
                        {"name": "CSS3 & Responsive Design", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "CSS3 controls visual presentation with Flexbox, Grid, animations, and media queries for responsive layouts.",
                                           "subtopics": ["Flexbox & Grid", "CSS Variables", "Animations & transitions", "Mobile-first design"],
                                           "free_resources": [{"title": "CSS Tricks Flexbox Guide", "url": "https://css-tricks.com/snippets/css/a-guide-to-flexbox/", "type": "Article"},
                                                              {"title": "Kevin Powell CSS", "url": "https://www.youtube.com/kepowob", "type": "Video"}]}},
                        {"name": "JavaScript ES6+", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Modern JavaScript with arrow functions, destructuring, modules, async/await, and DOM manipulation.",
                                           "subtopics": ["Arrow functions & template literals", "Promises & async/await", "Array methods (map, filter, reduce)", "ES modules"],
                                           "free_resources": [{"title": "JavaScript.info", "url": "https://javascript.info/", "type": "Documentation"},
                                                              {"title": "Traversy Media JS Crash Course", "url": "https://www.youtube.com/watch?v=hdI2bqOjy3c", "type": "Video"}]}},
                    ]
                },
                {
                    "phase_id": 2, "title": "Frontend Framework", "duration_weeks": 4,
                    "description": "Build dynamic, component-based UIs with React.",
                    "topics": [
                        {"name": "React Fundamentals", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "React is a declarative UI library for building interactive interfaces using components, JSX, and virtual DOM.",
                                           "subtopics": ["JSX & components", "Props & state", "Event handling", "Conditional rendering"],
                                           "free_resources": [{"title": "React Official Tutorial", "url": "https://react.dev/learn", "type": "Documentation"},
                                                              {"title": "Scrimba React Course", "url": "https://scrimba.com/learn/learnreact", "type": "Course"}]}},
                        {"name": "State Management & Hooks", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "React Hooks (useState, useEffect, useContext) manage component state and side effects without class components.",
                                           "subtopics": ["useState & useEffect", "useContext & useReducer", "Custom hooks", "React Query"],
                                           "free_resources": [{"title": "React Hooks Docs", "url": "https://react.dev/reference/react", "type": "Documentation"}]}},
                        {"name": "TypeScript", "status": "recommended", "priority": "medium",
                         "drawer_content": {"definition": "TypeScript adds static typing to JavaScript, catching errors at compile time and improving developer experience.",
                                           "subtopics": ["Type annotations", "Interfaces & types", "Generics", "TypeScript with React"],
                                           "free_resources": [{"title": "TypeScript Handbook", "url": "https://www.typescriptlang.org/docs/handbook/", "type": "Documentation"}]}},
                    ]
                },
                {
                    "phase_id": 3, "title": "Backend Development", "duration_weeks": 4,
                    "description": "Build robust server-side applications and APIs.",
                    "topics": [
                        {"name": "Node.js & Express", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Node.js runs JavaScript on the server. Express.js is a minimal framework for building RESTful APIs and web applications.",
                                           "subtopics": ["HTTP servers", "Routing & middleware", "Error handling", "File uploads"],
                                           "free_resources": [{"title": "Node.js Official Guide", "url": "https://nodejs.org/en/docs/guides", "type": "Documentation"},
                                                              {"title": "Express.js Guide", "url": "https://expressjs.com/en/guide/routing.html", "type": "Documentation"}]}},
                        {"name": "REST API Design", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "RESTful APIs use HTTP methods (GET, POST, PUT, DELETE) with consistent endpoints and JSON responses.",
                                           "subtopics": ["HTTP methods & status codes", "Request validation", "Authentication (JWT)", "API versioning"],
                                           "free_resources": [{"title": "REST API Tutorial", "url": "https://restfulapi.net/", "type": "Article"}]}},
                        {"name": "Database (PostgreSQL/MongoDB)", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "PostgreSQL is a powerful relational database, while MongoDB is a flexible NoSQL document store. Both are essential for full-stack apps.",
                                           "subtopics": ["SQL fundamentals", "Schema design", "ORM (Prisma/Sequelize)", "Indexing & optimization"],
                                           "free_resources": [{"title": "PostgreSQL Tutorial", "url": "https://www.postgresqltutorial.com/", "type": "Documentation"}]}},
                    ]
                },
                {
                    "phase_id": 4, "title": "DevOps & Deployment", "duration_weeks": 3,
                    "description": "Ship your applications to production with confidence.",
                    "topics": [
                        {"name": "Git & GitHub", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Git is a version control system. GitHub enables collaboration, code review, and CI/CD pipelines.",
                                           "subtopics": ["Branching strategies", "Pull requests", "GitHub Actions", "Collaboration workflows"],
                                           "free_resources": [{"title": "GitHub Skills", "url": "https://skills.github.com/", "type": "Course"}]}},
                        {"name": "Docker & Cloud Deployment", "status": "recommended", "priority": "medium",
                         "drawer_content": {"definition": "Docker containerizes applications for consistent deployment. Cloud platforms (AWS/GCP/Render) host them at scale.",
                                           "subtopics": ["Dockerfile basics", "Docker Compose", "Cloud hosting (Render/Vercel)", "Environment variables"],
                                           "free_resources": [{"title": "Docker Getting Started", "url": "https://docs.docker.com/get-started/", "type": "Documentation"}]}},
                    ]
                },
            ],
            "milestones": [
                {"after_phase": 1, "title": "First Web Page", "description": "Build a responsive portfolio website"},
                {"after_phase": 2, "title": "React App", "description": "Build a fully interactive single-page application"},
                {"after_phase": 3, "title": "Full Stack App", "description": "Create a complete full-stack application with authentication"},
                {"after_phase": 4, "title": "Deployed Project", "description": "Ship a production-ready app to the cloud"},
            ]
        },
        "data-scientist": {
            "goal": "Data Scientist",
            "icon": "📊",
            "estimated_weeks": 20,
            "description": "From Python fundamentals to deep learning, covering statistics, machine learning, and model deployment.",
            "phases": [
                {
                    "phase_id": 1, "title": "Python & Statistics", "duration_weeks": 5,
                    "description": "Build a strong foundation in Python programming and statistical thinking.",
                    "topics": [
                        {"name": "Python for Data Science", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Python is the primary language for data science, with rich libraries for analysis, visualization, and machine learning.",
                                           "subtopics": ["NumPy arrays", "Pandas DataFrames", "Data cleaning", "File I/O (CSV, JSON)"],
                                           "free_resources": [{"title": "Python Data Science Handbook", "url": "https://jakevdp.github.io/PythonDataScienceHandbook/", "type": "Documentation"}]}},
                        {"name": "Statistics & Probability", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Understanding distributions, hypothesis testing, and probability is essential for making data-driven decisions.",
                                           "subtopics": ["Descriptive statistics", "Probability distributions", "Hypothesis testing", "Correlation & regression"],
                                           "free_resources": [{"title": "Khan Academy Statistics", "url": "https://www.khanacademy.org/math/statistics-probability", "type": "Course"}]}},
                        {"name": "Data Visualization", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Effective visualization communicates insights clearly using charts, plots, and dashboards.",
                                           "subtopics": ["Matplotlib & Seaborn", "Plotly interactive charts", "Dashboard design", "Storytelling with data"],
                                           "free_resources": [{"title": "Matplotlib Tutorials", "url": "https://matplotlib.org/stable/tutorials/index.html", "type": "Documentation"}]}},
                    ]
                },
                {
                    "phase_id": 2, "title": "Machine Learning", "duration_weeks": 6,
                    "description": "Master core ML algorithms and the model development lifecycle.",
                    "topics": [
                        {"name": "Supervised Learning", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Supervised learning trains models on labeled data for classification (spam detection) and regression (price prediction).",
                                           "subtopics": ["Linear/logistic regression", "Decision trees & random forests", "SVM", "Model evaluation metrics"],
                                           "free_resources": [{"title": "Scikit-learn Tutorials", "url": "https://scikit-learn.org/stable/tutorial/", "type": "Documentation"}]}},
                        {"name": "Unsupervised Learning", "status": "recommended", "priority": "medium",
                         "drawer_content": {"definition": "Unsupervised learning discovers hidden patterns in unlabeled data through clustering and dimensionality reduction.",
                                           "subtopics": ["K-Means clustering", "PCA", "DBSCAN", "Anomaly detection"],
                                           "free_resources": [{"title": "Google ML Crash Course", "url": "https://developers.google.com/machine-learning/crash-course", "type": "Course"}]}},
                        {"name": "Feature Engineering", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Creating meaningful features from raw data is often the difference between a mediocre and an excellent model.",
                                           "subtopics": ["Missing value handling", "Encoding categorical variables", "Feature scaling", "Feature selection"],
                                           "free_resources": [{"title": "Kaggle Feature Engineering", "url": "https://www.kaggle.com/learn/feature-engineering", "type": "Course"}]}},
                    ]
                },
                {
                    "phase_id": 3, "title": "Deep Learning & NLP", "duration_weeks": 5,
                    "description": "Explore neural networks, computer vision, and natural language processing.",
                    "topics": [
                        {"name": "Neural Networks & TensorFlow", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Deep learning uses multi-layer neural networks for complex pattern recognition in images, text, and more.",
                                           "subtopics": ["Perceptrons & backpropagation", "CNNs for images", "RNNs for sequences", "Transfer learning"],
                                           "free_resources": [{"title": "TensorFlow Tutorials", "url": "https://www.tensorflow.org/tutorials", "type": "Documentation"}]}},
                        {"name": "NLP & Transformers", "status": "recommended", "priority": "medium",
                         "drawer_content": {"definition": "Natural Language Processing enables machines to understand text. Transformers (BERT, GPT) are the state of the art.",
                                           "subtopics": ["Text preprocessing", "Word embeddings", "Attention mechanism", "Hugging Face Transformers"],
                                           "free_resources": [{"title": "Hugging Face NLP Course", "url": "https://huggingface.co/learn/nlp-course", "type": "Course"}]}},
                    ]
                },
                {
                    "phase_id": 4, "title": "MLOps & Deployment", "duration_weeks": 4,
                    "description": "Deploy and monitor ML models in production.",
                    "topics": [
                        {"name": "Model Deployment (Flask/FastAPI)", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Serve ML models as REST APIs using Flask or FastAPI for real-time predictions.",
                                           "subtopics": ["Model serialization (pickle/joblib)", "REST API endpoints", "Docker containerization", "Cloud deployment"],
                                           "free_resources": [{"title": "FastAPI ML Tutorial", "url": "https://fastapi.tiangolo.com/tutorial/", "type": "Documentation"}]}},
                        {"name": "Experiment Tracking", "status": "alternative", "priority": "medium",
                         "drawer_content": {"definition": "Track experiments, metrics, and model versions using tools like MLflow and Weights & Biases.",
                                           "subtopics": ["MLflow tracking", "Model registry", "A/B testing", "Monitoring & drift detection"],
                                           "free_resources": [{"title": "MLflow Quickstart", "url": "https://mlflow.org/docs/latest/quickstarts/", "type": "Documentation"}]}},
                    ]
                },
            ],
            "milestones": [
                {"after_phase": 1, "title": "EDA Project", "description": "Complete an exploratory data analysis on a real dataset"},
                {"after_phase": 2, "title": "ML Model", "description": "Build and evaluate a predictive model on Kaggle"},
                {"after_phase": 3, "title": "Deep Learning Project", "description": "Train a neural network for image or text classification"},
                {"after_phase": 4, "title": "Deployed ML App", "description": "Deploy a model as a live API with monitoring"},
            ]
        },
        "backend-developer": {
            "goal": "Backend Developer",
            "icon": "🔧",
            "estimated_weeks": 18,
            "description": "Master server-side programming, database design, API architecture, and cloud deployment.",
            "phases": [
                {
                    "phase_id": 1, "title": "Programming Foundations", "duration_weeks": 4,
                    "description": "Build strong programming fundamentals in Python or Node.js.",
                    "topics": [
                        {"name": "Python / Node.js", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Choose Python (Django/Flask) or Node.js (Express) as your primary backend language. Both are industry standards.",
                                           "subtopics": ["Data structures & algorithms", "OOP principles", "Error handling", "Testing basics"],
                                           "free_resources": [{"title": "Automate the Boring Stuff", "url": "https://automatetheboringstuff.com/", "type": "Documentation"}]}},
                        {"name": "Data Structures & Algorithms", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Understanding arrays, trees, graphs, and common algorithms is essential for building efficient backends and acing interviews.",
                                           "subtopics": ["Arrays & linked lists", "Trees & graphs", "Sorting & searching", "Big O notation"],
                                           "free_resources": [{"title": "NeetCode DSA Roadmap", "url": "https://neetcode.io/roadmap", "type": "Course"}]}},
                    ]
                },
                {
                    "phase_id": 2, "title": "Databases & SQL", "duration_weeks": 4,
                    "description": "Design schemas, write complex queries, and manage data at scale.",
                    "topics": [
                        {"name": "SQL & PostgreSQL", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "SQL is the standard language for relational databases. PostgreSQL is powerful, open-source, and production-ready.",
                                           "subtopics": ["JOINs & subqueries", "Indexing & performance", "Transactions & ACID", "Schema migration"],
                                           "free_resources": [{"title": "SQLBolt Interactive", "url": "https://sqlbolt.com/", "type": "Course"}]}},
                        {"name": "NoSQL (Redis / MongoDB)", "status": "alternative", "priority": "medium",
                         "drawer_content": {"definition": "NoSQL databases offer flexible schemas for caching (Redis), document storage (MongoDB), and high-throughput workloads.",
                                           "subtopics": ["Document vs key-value stores", "Redis caching patterns", "MongoDB aggregation", "When to use NoSQL"],
                                           "free_resources": [{"title": "MongoDB University", "url": "https://university.mongodb.com/", "type": "Course"}]}},
                    ]
                },
                {
                    "phase_id": 3, "title": "APIs & Authentication", "duration_weeks": 4,
                    "description": "Build secure, scalable APIs with authentication and authorization.",
                    "topics": [
                        {"name": "RESTful API Design", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Design clean, consistent REST APIs with proper HTTP methods, status codes, pagination, and error handling.",
                                           "subtopics": ["Resource naming conventions", "Pagination & filtering", "Rate limiting", "API documentation (Swagger)"],
                                           "free_resources": [{"title": "REST API Design Guide", "url": "https://restfulapi.net/", "type": "Article"}]}},
                        {"name": "Authentication & Security", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Implement JWT tokens, OAuth 2.0, session management, and security best practices to protect your APIs.",
                                           "subtopics": ["JWT & refresh tokens", "OAuth 2.0 flows", "Password hashing (bcrypt)", "CORS & CSRF protection"],
                                           "free_resources": [{"title": "OWASP Top 10", "url": "https://owasp.org/www-project-top-ten/", "type": "Article"}]}},
                    ]
                },
                {
                    "phase_id": 4, "title": "System Design & DevOps", "duration_weeks": 6,
                    "description": "Scale systems and deploy with CI/CD pipelines.",
                    "topics": [
                        {"name": "System Design Basics", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Design scalable systems with load balancing, caching, message queues, and microservice architecture patterns.",
                                           "subtopics": ["Load balancers", "Caching strategies", "Message queues (RabbitMQ)", "Microservices vs monolith"],
                                           "free_resources": [{"title": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer", "type": "Documentation"}]}},
                        {"name": "Docker & CI/CD", "status": "recommended", "priority": "high",
                         "drawer_content": {"definition": "Containerize applications with Docker and automate testing and deployment with CI/CD pipelines.",
                                           "subtopics": ["Dockerfile & Docker Compose", "GitHub Actions CI/CD", "Cloud deployment", "Monitoring & logging"],
                                           "free_resources": [{"title": "Docker Docs", "url": "https://docs.docker.com/get-started/", "type": "Documentation"}]}},
                    ]
                },
            ],
            "milestones": [
                {"after_phase": 1, "title": "CLI Application", "description": "Build a command-line tool with proper structure"},
                {"after_phase": 2, "title": "Database Project", "description": "Design and implement a multi-table database schema"},
                {"after_phase": 3, "title": "Secure API", "description": "Build a production-grade REST API with authentication"},
                {"after_phase": 4, "title": "Deployed System", "description": "Deploy a containerized backend with CI/CD pipeline"},
            ]
        },
    }
    return roadmaps.get(slug)

