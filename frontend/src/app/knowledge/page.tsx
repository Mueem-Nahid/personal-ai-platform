"use client";

import { useProfiles } from "@/hooks/useProfiles";
import { PageHeader } from "@/components/organisms/PageHeader";
import { ProfileSelector } from "@/components/organisms/ProfileSelector";
import { ErrorBanner } from "@/components/organisms/ErrorBanner";
import { KnowledgeBase } from "@/components/organisms/KnowledgeBase";

export default function KnowledgePage() {
  const {
    profiles,
    selectedProfile,
    setSelectedProfile,
    loading,
    error,
    createProfile,
    clearError,
  } = useProfiles();

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
      <ErrorBanner error={error} onDismiss={clearError} />

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
