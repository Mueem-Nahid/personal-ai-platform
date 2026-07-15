"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api-client";
import type { Profile, Skill } from "@/lib/types";
import { PageHeader } from "@/components/organisms/PageHeader";
import { ProfileSelector } from "@/components/organisms/ProfileSelector";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { BasicInfoForm } from "@/components/organisms/BasicInfoForm";
import { SkillsEditor } from "@/components/organisms/SkillsEditor";
import { SectionCard } from "@/components/organisms/SectionCard";

export default function ProfilePage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [selectedProfile, setSelectedProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfiles = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.listProfiles();
      setProfiles(data);
      if (data.length > 0 && !selectedProfile) {
        setSelectedProfile(data[0]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load profiles");
    } finally {
      setLoading(false);
    }
  }, [selectedProfile]);

  useEffect(() => {
    loadProfiles();
  }, [loadProfiles]);

  const createProfile = async () => {
    try {
      const profile = await api.createProfile({
        full_name: "New User",
        experiences: [],
        projects: [],
        education: [],
        skills: [],
        certificates: [],
        achievements: [],
        publications: [],
        languages: [],
      });
      setProfiles((prev) => [...prev, profile]);
      setSelectedProfile(profile);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to create profile");
    }
  };

  const updateField = async (field: keyof Profile, value: string) => {
    if (!selectedProfile?.id) return;
    try {
      const updated = await api.updateProfile(selectedProfile.id, { [field]: value });
      setSelectedProfile(updated);
      setProfiles((prev) => prev.map((p) => (p.id === updated.id ? updated : p)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update profile");
    }
  };

  const addSkill = async () => {
    if (!selectedProfile?.id) return;
    try {
      const skill = await api.createSkill(selectedProfile.id, {
        name: "New Skill",
        category: "",
        proficiency: "intermediate",
      });
      setSelectedProfile((prev) =>
        prev ? { ...prev, skills: [...(prev.skills ?? []), skill] } : prev
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add skill");
    }
  };

  const updateSkill = async (skill: Skill, field: keyof Skill, value: string) => {
    if (!selectedProfile?.id || !skill.id) return;
    try {
      const updated = await api.updateSkill(selectedProfile.id, skill.id, { [field]: value });
      setSelectedProfile((prev) =>
        prev
          ? { ...prev, skills: prev.skills?.map((s) => (s.id === updated.id ? updated : s)) }
          : prev
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update skill");
    }
  };

  const deleteSkill = async (skillId: string) => {
    if (!selectedProfile?.id) return;
    try {
      await api.deleteSkill(selectedProfile.id, skillId);
      setSelectedProfile((prev) =>
        prev ? { ...prev, skills: prev.skills?.filter((s) => s.id !== skillId) } : prev
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete skill");
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-lg opacity-70">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Profile Editor" backHref="/" />

      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <ProfileSelector
        profiles={profiles}
        selectedId={selectedProfile?.id ?? ""}
        onSelect={setSelectedProfile}
        onCreate={createProfile}
      />

      {selectedProfile && (
        <div className="mt-6 space-y-6">
          <SectionCard title="Basic Info">
            <BasicInfoForm profile={selectedProfile} onChange={updateField} />
          </SectionCard>

          <SectionCard title="Skills">
            <SkillsEditor
              skills={selectedProfile.skills ?? []}
              onAdd={addSkill}
              onChange={updateSkill}
              onDelete={deleteSkill}
            />
          </SectionCard>

          <SectionCard title="Other Sections">
            <p className="text-sm opacity-50">
              Experience, Projects, Education, Certificates, Achievements, Publications, and Languages
              are available via the API. Full UI for these sections will be added in the next iteration.
            </p>
            <div className="mt-3 flex flex-wrap gap-4 text-sm">
              <span>Experiences: {selectedProfile.experiences?.length ?? 0}</span>
              <span>Projects: {selectedProfile.projects?.length ?? 0}</span>
              <span>Education: {selectedProfile.education?.length ?? 0}</span>
              <span>Certificates: {selectedProfile.certificates?.length ?? 0}</span>
              <span>Achievements: {selectedProfile.achievements?.length ?? 0}</span>
              <span>Publications: {selectedProfile.publications?.length ?? 0}</span>
              <span>Languages: {selectedProfile.languages?.length ?? 0}</span>
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}
