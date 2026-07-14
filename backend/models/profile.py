from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base
from models.mixins import TimestampMixin, UUIDMixin


class Profile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "profiles"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)

    experiences: Mapped[list[Experience]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Experience.start_date.desc()"
    )
    projects: Mapped[list[Project]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Project.start_date.desc()"
    )
    education: Mapped[list[Education]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Education.start_date.desc()"
    )
    skills: Mapped[list[Skill]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Skill.category"
    )
    certificates: Mapped[list[Certificate]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Certificate.issue_date.desc()"
    )
    achievements: Mapped[list[Achievement]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Achievement.event_date.desc()"
    )
    publications: Mapped[list[Publication]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Publication.event_date.desc()"
    )
    languages: Mapped[list[Language]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", order_by="Language.name"
    )


class Experience(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "experiences"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    bullet_points: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="experiences")


class Project(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    tech_stack: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    bullet_points: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="projects")


class Education(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "education"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    degree: Mapped[str | None] = mapped_column(String(255), nullable=True)
    field_of_study: Mapped[str | None] = mapped_column(String(255), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gpa: Mapped[str | None] = mapped_column(String(10), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="education")


class Skill(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "skills"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    proficiency: Mapped[str | None] = mapped_column(String(20), nullable=True)
    years_of_experience: Mapped[float | None] = mapped_column(Float, nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="skills")


class Certificate(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "certificates"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credential_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="certificates")


class Achievement(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "achievements"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="achievements")


class Publication(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "publications"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    authors: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="publications")


class Language(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "languages"

    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    proficiency: Mapped[str | None] = mapped_column(String(20), nullable=True)

    profile: Mapped[Profile] = relationship(back_populates="languages")
