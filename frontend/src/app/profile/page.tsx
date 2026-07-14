"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api-client";
import type { Profile, Skill } from "@/lib/types";

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
          ? {
              ...prev,
              skills: prev.skills?.map((s) => (s.id === updated.id ? updated : s)),
            }
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
        prev
          ? { ...prev, skills: prev.skills?.filter((s) => s.id !== skillId) }
          : prev
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete skill");
    }
  };

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center p-8">
        <p className="text-lg opacity-70">Loading...</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl p-8">
      <h1 className="mb-6 text-3xl font-bold">Profile Editor</h1>

      {error && (
        <div className="mb-4 rounded border border-red-400 bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950">
          {error}
          <button className="ml-2 underline" onClick={() => setError(null)}>dismiss</button>
        </div>
      )}

      <div className="mb-6 flex items-center gap-4">
        <select
          className="rounded border px-3 py-2 dark:bg-gray-800 dark:text-white"
          value={selectedProfile?.id ?? ""}
          onChange={(e) => {
            const p = profiles.find((p) => p.id === e.target.value);
            if (p) setSelectedProfile(p);
          }}
        >
          {profiles.map((p) => (
            <option key={p.id} value={p.id}>
              {p.full_name} {p.title ? `— ${p.title}` : ""}
            </option>
          ))}
        </select>
        <button
          className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
          onClick={createProfile}
        >
          + New Profile
        </button>
      </div>

      {selectedProfile && (
        <div className="space-y-8">
          <section className="rounded-lg border p-6 dark:border-gray-700">
            <h2 className="mb-4 text-xl font-semibold">Basic Info</h2>
            <div className="grid grid-cols-2 gap-4">
              <Field label="Full Name" value={selectedProfile.full_name ?? ""} onChange={(v) => updateField("full_name", v)} />
              <Field label="Title" value={selectedProfile.title ?? ""} onChange={(v) => updateField("title", v)} />
              <Field label="Email" value={selectedProfile.email ?? ""} onChange={(v) => updateField("email", v)} />
              <Field label="Phone" value={selectedProfile.phone ?? ""} onChange={(v) => updateField("phone", v)} />
              <Field label="Location" value={selectedProfile.location ?? ""} onChange={(v) => updateField("location", v)} />
              <Field label="Website" value={selectedProfile.website ?? ""} onChange={(v) => updateField("website", v)} />
              <Field label="GitHub URL" value={selectedProfile.github_url ?? ""} onChange={(v) => updateField("github_url", v)} />
              <Field label="LinkedIn URL" value={selectedProfile.linkedin_url ?? ""} onChange={(v) => updateField("linkedin_url", v)} />
              <div className="col-span-2">
                <label className="mb-1 block text-sm font-medium">Summary</label>
                <textarea
                  className="w-full rounded border px-3 py-2 dark:bg-gray-800 dark:text-white"
                  rows={3}
                  value={selectedProfile.summary ?? ""}
                  onChange={(e) => updateField("summary", e.target.value)}
                />
              </div>
            </div>
          </section>

          <section className="rounded-lg border p-6 dark:border-gray-700">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-semibold">Skills</h2>
              <button className="text-sm text-blue-600 hover:underline" onClick={addSkill}>
                + Add Skill
              </button>
            </div>
            <div className="space-y-2">
              {selectedProfile.skills?.map((skill) => (
                <div key={skill.id} className="flex items-center gap-2">
                  <input
                    className="flex-1 rounded border px-2 py-1 text-sm dark:bg-gray-800 dark:text-white"
                    value={skill.name}
                    onChange={(e) => updateSkill(skill, "name", e.target.value)}
                  />
                  <input
                    className="w-32 rounded border px-2 py-1 text-sm dark:bg-gray-800 dark:text-white"
                    placeholder="Category"
                    value={skill.category ?? ""}
                    onChange={(e) => updateSkill(skill, "category", e.target.value)}
                  />
                  <select
                    className="w-32 rounded border px-2 py-1 text-sm dark:bg-gray-800 dark:text-white"
                    value={skill.proficiency ?? ""}
                    onChange={(e) => updateSkill(skill, "proficiency", e.target.value)}
                  >
                    <option value="">Proficiency</option>
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                    <option value="expert">Expert</option>
                  </select>
                  <button
                    className="text-sm text-red-600 hover:underline"
                    onClick={() => skill.id && deleteSkill(skill.id)}
                  >
                    Delete
                  </button>
                </div>
              ))}
              {!selectedProfile.skills?.length && (
                <p className="text-sm opacity-50">No skills yet. Click &quot;Add Skill&quot; to get started.</p>
              )}
            </div>
          </section>

          <section className="rounded-lg border p-6 dark:border-gray-700">
            <h2 className="mb-2 text-xl font-semibold">Other Sections</h2>
            <p className="text-sm opacity-50">
              Experience, Projects, Education, Certificates, Achievements, Publications, and Languages
              are available via the API. Full UI for these sections will be added in the next iteration.
            </p>
            <div className="mt-3 flex gap-4 text-sm">
              <span>Experiences: {selectedProfile.experiences?.length ?? 0}</span>
              <span>Projects: {selectedProfile.projects?.length ?? 0}</span>
              <span>Education: {selectedProfile.education?.length ?? 0}</span>
              <span>Certificates: {selectedProfile.certificates?.length ?? 0}</span>
              <span>Achievements: {selectedProfile.achievements?.length ?? 0}</span>
              <span>Publications: {selectedProfile.publications?.length ?? 0}</span>
              <span>Languages: {selectedProfile.languages?.length ?? 0}</span>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="mb-1 block text-sm font-medium">{label}</label>
      <input
        className="w-full rounded border px-3 py-2 dark:bg-gray-800 dark:text-white"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
