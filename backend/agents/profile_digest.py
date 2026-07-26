from __future__ import annotations

from models.profile import Profile

_PII_FIELDS = frozenset(
    {
        "full_name",
        "email",
        "phone",
        "github_url",
        "linkedin_url",
        "website",
    }
)


def build_digest(profile: Profile) -> str:
    sections: list[str] = []

    if profile.title:
        sections.append(f"Title: {profile.title}")
    if profile.summary:
        sections.append(f"Summary: {profile.summary}")
    sections.append(f"Location: {profile.location}" if profile.location else "Location: unknown")

    if profile.skills:
        lines = ["## Skills"]
        for skill in profile.skills:
            parts = [f"- {skill.name}"]
            if skill.category:
                parts.append(f"   category: {skill.category}")
            if skill.proficiency:
                parts.append(f"   proficiency: {skill.proficiency}")
            if skill.years_of_experience is not None:
                parts.append(f"   years: {skill.years_of_experience}")
            lines.append("\n".join(parts))
        sections.append("\n".join(lines))

    if profile.experiences:
        lines = ["## Experience"]
        for exp in profile.experiences:
            parts = [f"- {exp.title} at {exp.company}"]
            if exp.employment_type:
                parts.append(f"   type: {exp.employment_type}")
            if exp.description:
                parts.append(f"   description: {exp.description}")
            if exp.bullet_points:
                parts.append("   highlights:")
                for bp in exp.bullet_points:
                    parts.append(f"     - {bp}")
            lines.append("\n".join(parts))
        sections.append("\n".join(lines))

    if profile.projects:
        lines = ["## Projects"]
        for proj in profile.projects:
            parts = [f"- {proj.name}"]
            if proj.description:
                parts.append(f"   description: {proj.description}")
            if proj.tech_stack:
                parts.append(f"   tech_stack: {', '.join(proj.tech_stack)}")
            if proj.bullet_points:
                parts.append("   highlights:")
                for bp in proj.bullet_points:
                    parts.append(f"     - {bp}")
            lines.append("\n".join(parts))
        sections.append("\n".join(lines))

    if profile.education:
        lines = ["## Education"]
        for edu in profile.education:
            degree = edu.degree or "Degree"
            field = edu.field_of_study or "unknown field"
            institution = edu.institution
            lines.append(f"- {degree} in {field} at {institution}")
        sections.append("\n".join(lines))

    if profile.certificates:
        lines = ["## Certificates"]
        for cert in profile.certificates:
            parts = [f"- {cert.name}"]
            if cert.issuer:
                parts.append(f"   issuer: {cert.issuer}")
            lines.append("\n".join(parts))
        sections.append("\n".join(lines))

    if profile.languages:
        lines = ["## Languages"]
        for lang in profile.languages:
            parts = [f"- {lang.name}"]
            if lang.proficiency:
                parts.append(f"   proficiency: {lang.proficiency}")
            lines.append("\n".join(parts))
        sections.append("\n".join(lines))

    if profile.achievements:
        lines = ["## Achievements"]
        for ach in profile.achievements:
            parts = [f"- {ach.title}"]
            if ach.description:
                parts.append(f"   description: {ach.description}")
            lines.append("\n".join(parts))
        sections.append("\n".join(lines))

    return "\n\n".join(sections)
