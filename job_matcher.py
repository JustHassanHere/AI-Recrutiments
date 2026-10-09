def match_cv_to_job(cv_text, job_skills):
    text = cv_text.lower()
    matched_skills = []
    missing_skills = []

    for skill in job_skills:
        if skill.lower() in text:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    score = 0
    if job_skills:
        score = round(len(matched_skills) / len(job_skills) * 100, 2)

    return {
        "score": score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
    }