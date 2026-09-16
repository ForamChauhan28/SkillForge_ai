"""Generate downloadable HTML career report."""
import json
from datetime import datetime


def generate_report_html(user, profile, roadmap, progress, certifications, projects):
    """Build a styled HTML career report from user data."""

    # Parse JSON fields safely
    def parse_json(data):
        if isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return {}
        return data or {}

    roadmap_data = parse_json(roadmap.get('raw_json', '{}')) if roadmap else {}
    cert_data = parse_json(roadmap.get('certifications_json', '{}')) if roadmap else {}
    proj_data = parse_json(roadmap.get('projects_json', '{}')) if roadmap else {}
    ats_data = parse_json(profile.get('ats_score_json', '{}')) if profile else {}

    skills = profile.get('extracted_skills', '') if profile else ''
    dream_job = profile.get('dream_job', 'Not specified') if profile else 'Not specified'

    # Build skills list
    skill_list = [s.strip() for s in skills.split(',') if s.strip()] if skills else []

    # Roadmap phases
    phases = roadmap_data.get('roadmap', {}).get('phases', [])
    est_weeks = roadmap_data.get('roadmap', {}).get('estimated_weeks', 'N/A')

    # Certifications
    certs = cert_data.get('certifications', [])

    # Projects
    projs = proj_data.get('projects', [])

    # ATS Score
    ats_score = ats_data.get('overall_score', 'N/A')

    now = datetime.now().strftime('%B %d, %Y')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Career Report - {user.get('name', 'Student')} | SkillForge AI</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', system-ui, sans-serif; color: #1a1a2e; line-height: 1.6; padding: 40px; max-width: 900px; margin: 0 auto; }}
        .header {{ text-align: center; padding: 30px 0; border-bottom: 3px solid #4a3f8a; margin-bottom: 30px; }}
        .header h1 {{ font-size: 2rem; color: #4a3f8a; }}
        .header p {{ color: #666; margin-top: 5px; }}
        .header .date {{ font-size: 0.85rem; color: #999; margin-top: 10px; }}
        .section {{ margin-bottom: 30px; page-break-inside: avoid; }}
        .section h2 {{ font-size: 1.3rem; color: #4a3f8a; border-bottom: 2px solid #ede7db; padding-bottom: 8px; margin-bottom: 15px; }}
        .profile-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
        .profile-item {{ background: #f5f0e8; padding: 15px; border-radius: 8px; }}
        .profile-item label {{ font-size: 0.8rem; color: #777; text-transform: uppercase; letter-spacing: 1px; }}
        .profile-item .value {{ font-size: 1.2rem; font-weight: 600; margin-top: 4px; }}
        .skill-tags {{ display: flex; flex-wrap: wrap; gap: 8px; }}
        .skill-tag {{ background: #4a3f8a; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; }}
        .phase-card {{ background: #f9f7f3; border-left: 4px solid #4a3f8a; padding: 15px; margin-bottom: 12px; border-radius: 0 8px 8px 0; }}
        .phase-card h3 {{ color: #4a3f8a; margin-bottom: 5px; }}
        .phase-topics {{ list-style: none; padding: 0; }}
        .phase-topics li {{ padding: 3px 0; padding-left: 20px; position: relative; }}
        .phase-topics li::before {{ content: "o"; position: absolute; left: 0; color: #c9a84c; }}
        .cert-item, .project-item {{ background: #f9f7f3; padding: 12px 15px; border-radius: 8px; margin-bottom: 8px; }}
        .cert-item strong, .project-item strong {{ color: #4a3f8a; }}
        .footer {{ text-align: center; margin-top: 40px; padding-top: 20px; border-top: 2px solid #ede7db; color: #999; font-size: 0.85rem; }}
        .score-circle {{ display: inline-block; width: 80px; height: 80px; border-radius: 50%; border: 4px solid #4a3f8a; text-align: center; line-height: 72px; font-size: 1.5rem; font-weight: 700; color: #4a3f8a; }}
        @media print {{ body {{ padding: 20px; }} .section {{ page-break-inside: avoid; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Career Readiness Report</h1>
        <p>{user.get('name', 'Student')} | SkillForge AI</p>
        <p class="date">Generated on {now}</p>
    </div>

    <div class="section">
        <h2>Profile Summary</h2>
        <div class="profile-grid">
            <div class="profile-item">
                <label>Name</label>
                <div class="value">{user.get('name', 'N/A')}</div>
            </div>
            <div class="profile-item">
                <label>Target Role</label>
                <div class="value">{dream_job}</div>
            </div>
            <div class="profile-item">
                <label>Skills Identified</label>
                <div class="value">{len(skill_list)}</div>
            </div>
            <div class="profile-item">
                <label>ATS Resume Score</label>
                <div class="value">{ats_score}/100</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Extracted Skills</h2>
        <div class="skill-tags">
            {''.join(f'<span class="skill-tag">{s}</span>' for s in skill_list) if skill_list else '<p>No skills extracted yet</p>'}
        </div>
    </div>
"""

    if phases:
        html += f"""
    <div class="section">
        <h2>Learning Roadmap ({est_weeks} weeks estimated)</h2>
"""
        for phase in phases:
            topics = phase.get('topics', [])
            topic_names = [t.get('name', '') if isinstance(t, dict) else str(t) for t in topics]
            html += f"""
        <div class="phase-card">
            <h3>Phase {phase.get('phase_id', '')}: {phase.get('title', '')}</h3>
            <p style="color: #666; font-size: 0.9rem;">{phase.get('duration_weeks', 'N/A')} weeks</p>
            <ul class="phase-topics">
                {''.join(f'<li>{t}</li>' for t in topic_names if t)}
            </ul>
        </div>
"""
        html += "    </div>\n"

    if certs:
        html += """
    <div class="section">
        <h2>Recommended Certifications</h2>
"""
        for cert in certs:
            html += f"""
        <div class="cert-item">
            <strong>{cert.get('name', '')}</strong> by {cert.get('issuing_body', '')}
            | Difficulty: {cert.get('difficulty', '')} | Cost: {cert.get('estimated_cost', 'N/A')}
        </div>
"""
        html += "    </div>\n"

    if projs:
        html += """
    <div class="section">
        <h2>Suggested Portfolio Projects</h2>
"""
        for proj in projs:
            tech = ', '.join(proj.get('tech_stack', []))
            html += f"""
        <div class="project-item">
            <strong>{proj.get('title', '')}</strong> ({proj.get('tier', '')})
            <p style="margin-top: 4px; font-size: 0.9rem;">{proj.get('description', '')}</p>
            <p style="font-size: 0.85rem; color: #666; margin-top: 4px;">Tech: {tech} | ~{proj.get('estimated_hours', 'N/A')} hours</p>
        </div>
"""
        html += "    </div>\n"

    if progress:
        html += f"""
    <div class="section">
        <h2>Progress Summary</h2>
        <div class="profile-grid">
            <div class="profile-item">
                <label>Overall Completion</label>
                <div class="value">{progress.get('percentage', 0)}%</div>
            </div>
            <div class="profile-item">
                <label>Topics Completed</label>
                <div class="value">{progress.get('completed_nodes', 0)} / {progress.get('total_nodes', 0)}</div>
            </div>
        </div>
    </div>
"""

    html += """
    <div class="footer">
        <p>Generated by SkillForge AI &mdash; Your AI-Powered Career Companion</p>
    </div>
</body>
</html>"""

    return html
