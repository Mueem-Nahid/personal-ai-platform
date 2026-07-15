"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api-client";
import type { Profile } from "@/lib/types";
import { PageHeader } from "@/components/organisms/PageHeader";
import { ProfileSelector } from "@/components/organisms/ProfileSelector";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { KnowledgeBase } from "@/components/organisms/KnowledgeBase";

export default function KnowledgePage() {
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

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-lg opacity-70">Loading...</p>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="Knowledge Base" backHref="/" />
      <ErrorBanner error={error} onDismiss={() => setError(null)} />

      <div className="mb-6">
        <ProfileSelector
          profiles={profiles}
          selectedId={selectedProfile?.id ?? ""}
          onSelect={setSelectedProfile}
          onCreate={createProfile}
        />
      </div>

      {selectedProfile?.id ? (
        <KnowledgeBase profileId={selectedProfile.id} />
      ) : (
        <p className="text-sm opacity-50">
          Select or create a profile above to manage your knowledge base.
        </p>
      )}
    </div>
  );
}
