"use client";

import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api-client";
import type { Profile, Skill } from "@/lib/types";
import { useProfiles } from "@/hooks/useProfiles";
import { useDebouncedCallback } from "@/hooks/useDebouncedCallback";
import { PageHeader } from "@/components/organisms/PageHeader";
import { ProfileSelector } from "@/components/organisms/ProfileSelector";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { BasicInfoForm } from "@/components/organisms/BasicInfoForm";
import { SkillsEditor } from "@/components/organisms/SkillsEditor";
import { SectionCard } from "@/components/organisms/SectionCard";

const DEBOUNCE_MS = 600;

export default function ProfilePage() {
  const {
    profiles,
    selectedProfile,
    setSelectedProfile,
    loading,
    error,
    createProfile,
    clearError,
    setError,
  } = useProfiles();

  const [localProfile, setLocalProfile] = useState<Profile | null>(null);
  const pendingSave = useRef<Partial<Profile>>({});

  useEffect(() => {
    setLocalProfile(selectedProfile);
    pendingSave.current = {};
    pendingSkillSaves.current.clear();
  }, [selectedProfile]);

  const saveToServer = useDebouncedCallback(async (profileId: string, data: Partial<Profile>) => {
    if (Object.keys(data).length === 0) return;
    try {
      const updated = await api.updateProfile(profileId, data);
      setSelectedProfile(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to update profile");
    }
  }, DEBOUNCE_MS);

  const updateField = (field: keyof Profile, value: string) => {
    if (!localProfile) return;
    setLocalProfile((prev) => (prev ? { ...prev, [field]: value } : prev));
    if (selectedProfile?.id) {
      pendingSave.current = { ...pendingSave.current, [field]: value };
      saveToServer(selectedProfile.id, pendingSave.current);
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
        prev ? { ...prev, skills: [...(prev.skills ?? []), skill] } : prev,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add skill");
    }
  };

  const pendingSkillSaves = useRef<Map<string, Partial<Skill>>>(new Map());

  const saveSkillToServer = useDebouncedCallback(
    async (profileId: string, skillId: string, data: Partial<Skill>) => {
      if (Object.keys(data).length === 0) return;
      try {
        await api.updateSkill(profileId, skillId, data);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to update skill");
      }
    },
    DEBOUNCE_MS,
  );

  const updateSkill = (skill: Skill, field: keyof Skill, value: string) => {
    if (!selectedProfile?.id || !skill.id) return;
    setSelectedProfile((prev) =>
      prev
        ? {
            ...prev,
            skills: prev.skills?.map((s) =>
              s.id === skill.id ? { ...s, [field]: value } : s,
            ),
          }
        : prev,
    );
    const existing = pendingSkillSaves.current.get(skill.id) ?? {};
    pendingSkillSaves.current.set(skill.id, { ...existing, [field]: value });
    saveSkillToServer(selectedProfile.id, skill.id, pendingSkillSaves.current.get(skill.id)!);
  };

  const deleteSkill = async (skillId: string) => {
    if (!selectedProfile?.id) return;
    try {
      await api.deleteSkill(selectedProfile.id, skillId);
      setSelectedProfile((prev) =>
        prev ? { ...prev, skills: prev.skills?.filter((s) => s.id !== skillId) } : prev,
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

      <ErrorBanner error={error} onDismiss={clearError} />

      <ProfileSelector
        profiles={profiles}
        selectedId={selectedProfile?.id ?? ""}
        onSelect={setSelectedProfile}
        onCreate={createProfile}
      />

      {localProfile && (
        <div className="mt-6 space-y-6">
          <SectionCard title="Basic Info">
            <BasicInfoForm profile={localProfile} onChange={updateField} />
          </SectionCard>

          <SectionCard title="Skills">
            <SkillsEditor
              skills={localProfile.skills ?? []}
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
              <span>Experiences: {localProfile.experiences?.length ?? 0}</span>
              <span>Projects: {localProfile.projects?.length ?? 0}</span>
              <span>Education: {localProfile.education?.length ?? 0}</span>
              <span>Certificates: {localProfile.certificates?.length ?? 0}</span>
              <span>Achievements: {localProfile.achievements?.length ?? 0}</span>
              <span>Publications: {localProfile.publications?.length ?? 0}</span>
              <span>Languages: {localProfile.languages?.length ?? 0}</span>
            </div>
          </SectionCard>
        </div>
      )}
    </div>
  );
}
