from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ExperienceBase(BaseModel):
    company: str
    title: str
    location: str | None = None
    employment_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    current: bool = False
    description: str | None = None
    bullet_points: list[str] | None = None


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(BaseModel):
    company: str | None = None
    title: str | None = None
    location: str | None = None
    employment_type: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    current: bool | None = None
    description: str | None = None
    bullet_points: list[str] | None = None


class ExperienceOut(ExperienceBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class ProjectBase(BaseModel):
    name: str
    description: str | None = None
    url: str | None = None
    tech_stack: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    bullet_points: list[str] | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    url: str | None = None
    tech_stack: list[str] | None = None
    start_date: date | None = None
    end_date: date | None = None
    bullet_points: list[str] | None = None


class ProjectOut(ProjectBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class EducationBase(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None
    description: str | None = None


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    gpa: str | None = None
    description: str | None = None


class EducationOut(EducationBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class SkillBase(BaseModel):
    name: str
    category: str | None = None
    proficiency: str | None = Field(None, description="beginner | intermediate | advanced | expert")
    years_of_experience: float | None = None


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    proficiency: str | None = None
    years_of_experience: float | None = None


class SkillOut(SkillBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class CertificateBase(BaseModel):
    name: str
    issuer: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    url: str | None = None


class CertificateCreate(CertificateBase):
    pass


class CertificateUpdate(BaseModel):
    name: str | None = None
    issuer: str | None = None
    issue_date: date | None = None
    expiry_date: date | None = None
    credential_id: str | None = None
    url: str | None = None


class CertificateOut(CertificateBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class AchievementBase(BaseModel):
    title: str
    description: str | None = None
    event_date: date | None = None
    category: str | None = None


class AchievementCreate(AchievementBase):
    pass


class AchievementUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    event_date: date | None = None
    category: str | None = None


class AchievementOut(AchievementBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class PublicationBase(BaseModel):
    title: str
    publisher: str | None = None
    event_date: date | None = None
    url: str | None = None
    description: str | None = None
    authors: list[str] | None = None


class PublicationCreate(PublicationBase):
    pass


class PublicationUpdate(BaseModel):
    title: str | None = None
    publisher: str | None = None
    event_date: date | None = None
    url: str | None = None
    description: str | None = None
    authors: list[str] | None = None


class PublicationOut(PublicationBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class LanguageBase(BaseModel):
    name: str
    proficiency: str | None = Field(None, description="basic | conversational | fluent | native")


class LanguageCreate(LanguageBase):
    pass


class LanguageUpdate(BaseModel):
    name: str | None = None
    proficiency: str | None = None


class LanguageOut(LanguageBase, ORMBase):
    id: UUID
    profile_id: UUID
    created_at: datetime
    updated_at: datetime


class ProfileBase(BaseModel):
    full_name: str
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    title: str | None = None
    summary: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    website: str | None = None


class ProfileCreate(ProfileBase):
    experiences: list[ExperienceCreate] = []
    projects: list[ProjectCreate] = []
    education: list[EducationCreate] = []
    skills: list[SkillCreate] = []
    certificates: list[CertificateCreate] = []
    achievements: list[AchievementCreate] = []
    publications: list[PublicationCreate] = []
    languages: list[LanguageCreate] = []


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    location: str | None = None
    title: str | None = None
    summary: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    website: str | None = None


class ProfileOut(ProfileBase, ORMBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    experiences: list[ExperienceOut] = []
    projects: list[ProjectOut] = []
    education: list[EducationOut] = []
    skills: list[SkillOut] = []
    certificates: list[CertificateOut] = []
    achievements: list[AchievementOut] = []
    publications: list[PublicationOut] = []
    languages: list[LanguageOut] = []
